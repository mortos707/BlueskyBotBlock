#!/usr/bin/env python3
# -*- mode: python -*-
# -*- coding: utf-8 -*-

'''

B3 - BlueSky Bot Block

'''

# @depends: boto3, python (>=3.8)
__author__ = 'jgrosch@gmail.com'
__copyright__ = "Copyright (c) 2025 Josef Grosch"
__description__ = ""
__usage__ = ""
__version__ = '0.1'

import os, sys
import json
import requests
import argparse
import toml
import sqlite3 as S3
import hashlib

# --------------------------------------------------------------------
#
# main
#
# --------------------------------------------------------------------
def main():
    RS = ReturnStatus
    pDict = {}
    pDict['S3'] = S3
    
    # The minimum version of python we support is 3.8
    min_python_version = (3, 8)
    if sys.version_info < min_python_version:
        print("Python %s.%s or later is required.\n" % min_python_version)
        sys.exit(RS.NOT_OK)

    toolName     = os.path.basename(__file__)
    version      = __version__
    notFoundList = []
    foundList    = []

    getEnvironVars(pDict)
    initTool(pDict)
    
    parser = argparse.ArgumentParser()

    """
    parser.add_argument('--clear_db', help='Whipe the DB clean.',
                        action='store_true')

    parser.add_argument('--backup_db', help='Backup the DB.',
                        action='store_true')
    """

    parser.add_argument('--block', help='Pick a group(s) to block', nargs='+')

    parser.add_argument('--debug', help='Turn on debug messages',
                        action='store_true')

    parser.add_argument('--do_check', help='Check handles against Bluesky',
                        action='store_true')

    parser.add_argument('--do_pull', help='Pull block list from SOA',
                        action='store_true')

    parser.add_argument('--list', help='List block categories',
                        action='store_true')
    
    parser.add_argument('--mute', help='Pick a group(s) to mute', nargs='+')
    
    parser.add_argument('--unblock', help='Pick a group(s) to unblock', nargs='+')

    parser.add_argument('--unmute', help='Pick a group(s) to unmute', nargs='+')

    parser.add_argument('--verbose', help='Turn on verbose output',
                        action='store_true')

    parser.add_argument('--version', help='Display the version',
                        action='store_true')

    args = parser.parse_args()
    pDict['args'] = args
    
    #
    # Spit out the version
    #
    if args.version:
        print(f"{toolName} - Version: {version}")
        sys.exit(RS.OK)

    #
    # List all the categories
    #
    if args.list:
        blockNames = pDict['BlockNames']
        print("\nDefined block categories")
        for entry in blockNames:
            print(f"    {entry}")
        print("\n")
        sys.exit(RS.OK)
        
    #
    # pull the latest block list from the master
    #
    if args.do_pull:
        try:
            r = requests.get(pDict['defaultMD5HashLink'])
            if r.status_code != 200:
                print(f"Error: {inLink} not found")
                sys.exit(RS.NOT_OK)
            else:
                tmpStr = r.text
                bits = tmpStr.split()
                fileMd5Hash = bits[0].strip()
                
            r = requests.get(pDict['defaultB3Link'])
            if r.status_code != 200:
                print(f"Error: {inLink} not found")
                sys.exit(RS.NOT_OK)
            else:
                jObj = r.json()
                xB3Str = r.text
                md5Obj = hashlib.md5()
                encodeStr = xB3Str.encode()
                md5Obj.update(encodeStr)
                md5Sum = md5Obj.hexdigest()

                if md5Sum != fileMd5Hash:
                    print("Error: file hash do not match")
                    print(f"Hash #1: {md5Sum}")
                    print(f"Hash #2: {fileMd5Hash}")
                    sys.exit(RS.NOT_OK)
                    
                pDict['jObj'] = jObj
        except (ConnectionError) as e:
            BP = 0

        pDict['Blocks'] = jObj['blocks']
        loadDB(pDict)

    BP = 0
    if args.block or args.do_check: 
        from atproto import Client, models
        from atproto.exceptions import BadRequestError
        
    if args.block:
        BP = 0
    # Check the DB against Bluesky
    BP = 0
    if args.do_check:
        blueSkyLogin  = pDict['blueSkyLogin']
        blueSkyPasswd = pDict['blueSkyPasswd']
        
        client = Client()
        client.login(blueSkyLogin, blueSkyPasswd)

        # TEST
        a1 = client.app
        a2 = client.app.bsky
        a3 = client.app.bsky.graph
        a4  = client.app.bsky.graph.block

        # AppBskyGraphBlockRecord
        
        for entry in a4:
            BP = 0

        for key in pDict['Blocks']:
            BL = pDict['Blocks'][key]
            for entry in BL:
                name = entry.strip()
                if '@' in name:
                    name = name.replace('@', '')
                try:
                    UD = client.get_profile(actor=name)
                except (BadRequestError) as e:
                    BP = 0
                    statusCode = e.response.status_code
                    if statusCode == 400:
                        notFoundList.append(name)
                        if args.debug:
                            print(f"Account: {name} NOT found")
                        continue
                BP = 0
                B3 = defineB3(UD)
                foundList.append(name)
                if args.debug:
                    print(f"Account: {name} found")
                # End of for loop
            BP = 1
        BP = 2
    BP = 3
    
    notFoundCount = len(notFoundList)
    foundCount    = len(foundList)
    accountTotal = notFoundCount + foundCount
    
    sys.exit(RS.OK)
    # End of main

# --------------------------------------------------------------------
#
# defineB3
#
# --------------------------------------------------------------------
def defineB3(result: dict) -> dict:
    """
    Args:
    Returns:
    """
    B3 = {}

    FieldList = pDict['dbFieldList']
    for index, key in enumerate(FieldList):
        value = result[0][index]
        if value is None:
            value = ''
        B3[key] = value
        
    return B3
    # defineB3
    
# --------------------------------------------------------------------
#
# loadDB
#
# --------------------------------------------------------------------
def loadDB(pDict: dict):
    """
    Args:
    Returns:
    """
    RS = ReturnStatus
    rDict = genReturnDict("Inside loadDB")
    
    jObj      = pDict['jObj']
    dbFile    = pDict['DB_FILE']
    S3        = pDict['S3']
    tableName = pDict['tableName']
    
    """
    CREATE TABLE IF NOT EXISTS 'B3' (
        'rec_num'       INTEGER, // record number
        'date_time'     TEXT,    // datetime stamp 12-Jan-2024 21:14:00
        'handle'        TEXT,    // handle to be blocked
        'status'        TEXT,    // blockd, muted, removed ?
        'block'         TEXT,    // block handle Y/N
        'mute'          TEXT,    // mute handle Y/N
        'active'        TEXT,    // is account active ?
        'block_group'   TEXT,    // block group ; spammer, asshole, etc.
        PRIMARY KEY('rec_num' AUTOINCREMENT)
    );
    """

    try:
        conn = S3.connect(dbFile)
        cur  = conn.cursor()
        pDict['conn'] = conn
        pDict['cur'] = cur

        query1 = (" select name from sqlite_master WHERE type='table'"
                 " and name = '{}'; ".format(tableName))
        listOfTables = cur.execute(query1).fetchall()
 
        if listOfTables == []:
            print('Table not found!')
            # create table

            createSQL = (
                
                ' CREATE TABLE IF NOT EXISTS "B3" ( '
                " 'rec_num'       INTEGER, "
                " 'date_time'     TEXT, "
                " 'handle'        TEXT, "
                " 'status'        TEXT, "
                " 'block'         TEXT, "
                " 'mute'          TEXT, "
                " 'active'        TEXT, "
                " 'block_group'   TEXT, "
                ' PRIMARY KEY("rec_num" AUTOINCREMENT));')

            createSQLList = [" BEGIN TRANSACTION; ",
                             " DROP TABLE IF EXISTS 'B3';",
                             createSQL
                             ]
            try:
                for line in createSQLList:
                    cur.execute(line)   
                    conn.commit()
            except (S3.OperationalError) as e:
                BP = 0
    except (S3.OperationalError) as e:
        BP = 1
        
    Blocks = jObj['blocks']
    for key in Blocks:
        if 'removed' in key:
            active = 'no'
        else:
            active = 'yes'
            
        BL = Blocks[key]
        for entry in BL:
            name = entry.strip()
            if '@' in name:
                name = name.replace('@', '')
            query2 = f" select * from {tableName} where account_name = \'{name}\';"
            result = cur.execute(query2).fetchall()
            if result == []:
                # user not found
                block_name   = key
                account_name = name
                status       = 'block'
                
                query3 = (" insert into B3 (account_name, status, block_name, "
                          " active) values ('{}', '{}', '{}', '{}'); "
                          .format(account_name, status, block_name, active))

                cur.execute(query3)
                conn.commit()

                BP = 5
            else:
                Bp = 6
                B3 = defineB3(result)
            BP = 2
        BP = 3
    BP = 4

    return
    # End of loadDB

# --------------------------------------------------------------------
#
# getEnvironVars
#
# --------------------------------------------------------------------
def getEnvironVars(pDict):
    """
    Args:
    Returns:
    """

    RS = ReturnStatus
    rDict = genReturnDict("Inside getEnvironVars")
    
    pDict['baseDir'] = os.environ['PWD']
    pDict['B3_HOME'] = os.environ.get('B3_HOME', pDict['baseDir'])

    pDict['DB_PATH'] = f"{pDict['baseDir']}/../data"
    pDict['B3_CONFIG_PATH'] = f"{pDict['B3_HOME']}/../etc" #/B3.toml"
    pDict['B3_CONFIG_FILE'] = f"{pDict['B3_CONFIG_PATH']}/B3.toml"
    
    pDict['blueSkyLogin']  = os.environ.get('blueSkyLogin', '')
    pDict['blueSkyPasswd'] = os.environ.get('blueSkyPasswd', '')
    
    #pDict['B3_CONFIG'] = f"{pDict['B3_CONFIG_PATH']}/B3.toml"
    if os.path.exists(pDict['B3_CONFIG_FILE']):
        with open(pDict['B3_CONFIG_FILE'], 'r') as fh:
            Lines = fh.read()

        cDict = toml.loads(Lines)
        Base = cDict['base']
        for key in Base:
            value = Base[key]
            pDict[key] = value

        pDict['cDict'] = cDict
        pDict['DB_FILE'] = f"{pDict['DB_PATH']}/{pDict['dbFileName']}" 
    else:
        pDict['cDict'] = {}

    rDict['msg'] = 'Enviornment vars loaded'
    
    return rDict
    # End of getEnvironVars

# --------------------------------------------------------------------
#
# genReturnDict
#
# --------------------------------------------------------------------
def genReturnDict(msg = "") -> dict:
    """
    This sets up a dictonary that is intented to be returned from
    a function call. The real value here is that this dictonary
    contains information, like the function name and line number,
    about the function. This is handy when debugging a mis-behaving
    function.

    Args:
        msg: A text string containg a simple, short message

    Returns:
        rDict: a dictonary that is returned from a function call

    """
    RS = ReturnStatus()

    rDict = {}

    # These values come from the previous stack frame ie. the
    # calling function.
    rDict['line_number']   = sys._getframe(1).f_lineno
    rDict['filename']      = sys._getframe(1).f_code.co_filename
    rDict['function_name'] = sys._getframe(1).f_code.co_name

    rDict['status']   = RS.OK # See the class ReturnStatus
    rDict['msg']      = msg   # The passed in string
    rDict['data']     = ''    # The data/json returned from func call
    rDict['path']     = ''    # FQPath to file created by func (optional)
    rDict['resource'] = ''    # What resource is being used (optional)

    return rDict
    # End of genReturnDict


# --------------------------------------------------------------------
#
# class ReturnStatus
#
# --------------------------------------------------------------------
class ReturnStatus:
    """
    Since we can't have nice things, like #define, this is
    a stand in.

    These values are intended to be returned from a function
    call. For example

    def bar():
        RS = ReturnStatus()
        rDict = genReturnDict('Demo program bar')

        i = 1 + 1

        if i == 2:
            rDict['status'] = RS.OK
        else:
            rDict['status'] = RS.NOT_OK
            rDict['msg'] = 'Basic math is broken'

        return rDict

    def foo():
        RS = ReturnStatus()

        rDict = bar()
        if rDict['status'] = RS.OK:
            print('All is right with the world')
        else:
            print('We're doomed!')
            print(rDict['msg'])
            sys.exit(RS.NOT_OK)

        return RS.OK

    """

    OK         = 0 # It all worked out
    NOT_OK     = 1 # Not so much
    SKIP       = 2 # We are skipping this block/func
    NOT_YET    = 3 # This block/func is not ready
    FAIL       = 4 # It all went to hell in a handbasket
    NOT_FOUND  = 5 # Could not find what we were looking for
    FOUND      = 6 # Found my keys
    YES        = 7 # Cant believe I missed these
    NO         = 8 #
    RESTRICTED = 9 #
    # End of class ReturnStatus

# --------------------------------------------------------------------
#
# initTool
#
# --------------------------------------------------------------------
def initTool(pDict):
    pDict['dbFieldList'] = ["rec_num", "date_time", "handle",
                            "status",  "block",     "mute",
                            "active",  "block_group"]

    pDict['BlockNames'] = ["crypto",   "jerk", "maga",
                           "onlyfans", "other", "removed",
                           "scammer"]

    return
    # End of initTool
    
# --------------------------------------------------------------------
#
# entry point
#
# --------------------------------------------------------------------
if __name__ == '__main__':
    main()
