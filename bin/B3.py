#!/usr/bin/env python3
# -*- mode: python -*-
# -*- coding: utf-8 -*-

'''

B3 - BlueSky Bot Block

'''

# @depends: boto3, python (>=3.8)
__author__ = 'jgrosch@gmail.com'
__copyright__ = "Copyright (c) 2025 Josef Grosch"
__description__ = "A tool to manage blocks and mutes in Bluesky"
__usage__ = "./B3.py --help"
__version__ = '0.2'

import os, sys

script_dir = os.path.dirname( __file__ )
mymodule_dir = os.path.join( script_dir, '..', 'lib' )
sys.path.append( mymodule_dir )

import bbblib

import json
import requests
import argparse
import toml
import sqlite3 as S3
import hashlib
import datetime

#from atproto import Client, models
#from atproto.exceptions import BadRequestError

# --------------------------------------------------------------------
#
# main
#
# --------------------------------------------------------------------
def main():
    """
    
    https://public.api.bsky.app/

    """
    
    RS = bbblib.ReturnStatus
    
    # The minimum version of python we support is 3.8
    min_python_version = (3, 8)
    if sys.version_info < min_python_version:
        print("Python %s.%s or later is required.\n" % min_python_version)
        sys.exit(RS.NOT_OK)

    #
    # Setup tool and deal with the arguments
    #
    pDict = initTool()

    #
    # User info @BlueSky
    #
    getUserInfo(pDict)
    
    rDict = processArgs(pDict)
    if rDict['status'] == RS.NOT_FOUND:
        parser = pDict['parser']
        parser.print_help()
        sys.exit(RS.NOT_OK)
    else:
        args = pDict['args']

    #
    # Spit out the version
    #
    if args.version:
        BP = 0
        rDict = printVersion(pDict)

    #
    # List all the categories
    #
    if args.list and not rDict['status'] == RS.CALL_EXIT:
        rDict = listCategories(pDict)
        
    #
    # pull the latest block list from the master
    #
    if args.doPull and not rDict['status'] == RS.CALL_EXIT:
        BP = 0
        rDict = doPull(pDict)

    #
    #
    #
    if args.updateDB and not rDict['status'] == RS.CALL_EXIT:
        BP = 0
        rDict = updateDB(pDict)

    #
    #
    #
    if args.block or args.doCheck:
        BP = 0

    #
    #
    #
    if args.block and not rDict['status'] == RS.CALL_EXIT:
        BP = 0
        rDict = doBlock(pDict)

    #
    # Check the DB against Bluesky
    #
    if args.doCheck and not rDict['status'] == RS.CALL_EXIT:
        BP = 0
        rDict = doCheck(pDict)
        
    #
    #
    #
    if args.clearDB and not rDict['status'] == RS.CALL_EXIT:
        BP = 0
        rDict = clearDB(pDict)

    #
    #
    #
    if args.backupDB and not rDict['status'] == RS.CALL_EXIT:
        BP = 0
        rDict = backupDB()
        
    #notFoundCount = len(notFoundList)
    #foundCount    = len(foundList)
    #accountTotal = notFoundCount + foundCount
    
    sys.exit(RS.OK)
    # End of main


# --------------------------------------------------------------------
#
# clearDB
#
# --------------------------------------------------------------------
def clearDB(pDict):
    """
    Args:
    Returns:
    """
    RS = pDict['RS']
    rDict = genReturnDict("Inside updateDB")

    tableName = pDict['tableName']
    #Delete from TableName
    query = f"delete from {tableName};"
    prompt = "Are you sure you want to delete the contents of the DB? [y|n] "
    if bbblib.yesNo(prompt):
        BP = 0
    else:
        BP = 1

    return rDict
    # End of clearDB

    
# --------------------------------------------------------------------
#
# updateDB
#
# --------------------------------------------------------------------
def updateDB(pDict: dict):
    """
    Args:
    Returns:
    """
    
    RS = pDict['RS']
    rDict = genReturnDict("Inside updateDB")

    args      = pDict['args']
    jObj      = pDict['jObj']
    dbFile    = pDict['DB_FILE']
    S3        = pDict['S3']
    tableName = pDict['tableName']

    doInsert = True
    
    """
    BEGIN TRANSACTION;
    DROP TABLE IF EXISTS 'B3';
    CREATE TABLE IF NOT EXISTS 'B3' (
           'rec_num'       INTEGER,
           'date_time'     TEXT,
           'handle'        TEXT,
           'status'        TEXT,
           'block'         TEXT,
           'mute'          TEXT,
           'active'        TEXT,
           'block_group'   TEXT,
           PRIMARY KEY('rec_num' AUTOINCREMENT)
    );
    COMMIT;
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
            query2 = f" select * from {tableName} where handle = \'{name}\';"
            result = cur.execute(query2).fetchall()
            if result == []:
                # user not found

                now = datetime.datetime.today()
                dateTime = now.strftime('%d-%b-%Y %H:%M:%S')
                handle     = name
                status     = 'new'
                block      = 'yes'
                mute       = 'no'
                blockGroup = key
                
                #query3 = (" insert into B3 (account_name, status, block_name, "
                #          " active) values ('{}', '{}', '{}', '{}'); "
                #          .format(account_name, status, block_name, active))

                query2 = (" insert into {} (date_time, handle, status, "
                          " block, mute, active, block_group) values ( "
                          " '{}', '{}', '{}', '{}', '{}', '{}', '{}'); "
                          .format(tableName, dateTime, handle, status, block,
                                  mute, active, blockGroup))

                if args.debug:
                    print(query2)

                if doInsert:
                    cur.execute(query2)
                    conn.commit()

                BP = 5
            else:
                # User found
                Bp = 6
            BP = 2
        BP = 3
    BP = 4

    return rDict
    # End of updateDB


# --------------------------------------------------------------------
#
# initTool
#
# --------------------------------------------------------------------
def initTool():
    """
    Args:
    Returns:
    """

    RS = bbblib.ReturnStatus
    rDict = bbblib.genReturnDict("Inside initTool")

    pDict = {}

    pDict['RS'] = RS
    pDict['S3'] = S3
    pDict['toolName'] = os.path.basename(__file__)
    pDict['version'] = __version__

    pDict['dbFieldList'] = ["rec_num", "date_time", "handle",
                            "status",  "block",     "mute",
                            "active",  "block_group"]

    pDict['BlockNames'] = ["crypto",   "jerk", "maga",
                           "onlyfans", "other", "removed",
                           "scammer"]
    
    pDict['baseDir'] = os.environ['PWD']
    pDict['B3_HOME'] = os.environ.get('B3_HOME', pDict['baseDir'])
    if pDict['B3_HOME'].endswith('/bin'):
        pDict['B3_HOME'] = pDict['B3_HOME'].replace('/bin', '')
    
    pDict['DB_PATH']   = f"{pDict['B3_HOME']}/data"
    pDict['DATA_PATH'] = pDict['DB_PATH']
    
    pDict['B3_CONFIG_PATH'] = f"{pDict['B3_HOME']}/etc" #/B3.toml"
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

    return pDict
    # End of initTool


# --------------------------------------------------------------------
#
# saveToFile
#
# --------------------------------------------------------------------
def saveToFile(pDict):
    """
    Args:
    Returns:
    """

    RS = pDict['RS']
    rDict = bbblib.genReturnDict("Inside saveToFile")
    
    fixedDateStr = pDict['latestDate'].replace(' ', '-')
    blockListFile = f"{pDict['DATA_PATH']}/B3BlockList.{fixedDateStr}.json"
    outStr = json.dumps(pDict['Blocks'], indent=4)
    
    with open(blockListFile, 'w') as fh:
        fh.write(outStr)

    md5Obj = hashlib.md5()
    encodeStr = outStr.encode()
    md5Obj.update(encodeStr)
    md5Sum = md5Obj.hexdigest()
    outStr = f"{md5Sum} B3BlockList.{fixedDateStr}.json\n"
    md5sumFile = f"{pDict['DATA_PATH']}/B3BlockList.{fixedDateStr}.md5sum"
    
    with open(md5sumFile, 'w') as fh:
        fh.write(outStr)

    return rDict
    # End of saveToFile


# --------------------------------------------------------------------
#
# processArgs
#
# --------------------------------------------------------------------
def processArgs(pDict):

    """
    Args:
    Return:
    """

    RS = pDict['RS']
    rDict = bbblib.genReturnDict("Inside processArgs")

    nonBinaryOptions = ['block', 'mute', 'unblock', 'unmute']
    nboCount = len(nonBinaryOptions)
    
    argSelectedCount = 0
    
    parser = argparse.ArgumentParser()

    parser.add_argument('--clearDB', help='Whipe the DB clean.',
                        action='store_true')

    parser.add_argument('--backupDB', help='Backup the DB.',
                        action='store_true')

    parser.add_argument('--block', help='Pick a group(s) to block', nargs='+')

    parser.add_argument('--debug', help='Turn on debug messages',
                        action='store_true')

    parser.add_argument('--doCheck', help='Check handles against Bluesky',
                        action='store_true')

    parser.add_argument('--doPull', help='Pull block list from SOT',
                        action='store_true')

    parser.add_argument('--list', help='List block categories',
                        action='store_true')
    
    parser.add_argument('--mute', help='Pick a group(s) to mute', nargs='+')
    
    parser.add_argument('--unblock', help='Pick a group(s) to unblock', nargs='+')

    parser.add_argument('--unmute', help='Pick a group(s) to unmute', nargs='+')

    parser.add_argument('--updateDB', help='Update DB with latest list',
                        action='store_true')

    parser.add_argument('--verbose', help='Turn on verbose output',
                        action='store_true')

    parser.add_argument('--version', help='Display the version',
                        action='store_true')

    args = parser.parse_args()
    pDict['parser'] = parser
    pDict['args'] = args

    trueCount  = 0
    paramCount = 0
    
    totalArgCount = len(args.__dict__)
    boCount = totalArgCount - nboCount
    for key in args.__dict__:
        value = args.__dict__[key]
        
        if key in nonBinaryOptions:
            if value is not None:
                BP = 0
                paramCount += 1
            else:
                BP = 1

            if isinstance(value, list):
                BP = 0
                continue
            
            if isinstance(value, dict):
                BP = 1
                continue
        else:
            BP = 0
            if value is True:
                trueCount += 1
        #

    if (trueCount == 0) and (paramCount == 0):
        rDict['status'] = RS.NOT_FOUND
        rDict['msg'] = 'No option selected, call help()'
        
    return rDict
    # End of processArgs

    
# --------------------------------------------------------------------
#
# getUserInfo
#
# --------------------------------------------------------------------
def getUserInfo(pDict):
    """
    Args:
    Returns:
    """
    RS = pDict['RS']
    rDict = bbblib.genReturnDict("Inside getUserInfo")

    if pDict['BSLib'] == RS.NO:
        from atproto import Client, models
        from atproto.exceptions import BadRequestError
        pDict['BSLib_loaded'] = RS.YES
    
    blueSkyLogin  = pDict['blueSkyLogin']
    blueSkyPasswd = pDict['blueSkyPasswd']

    client = Client()
    client.login(blueSkyLogin, blueSkyPasswd)

    # UD - User Data
    UD = client.me

    ME = bbblib.defineME(UD)
    pDict['ME'] = ME

    return rDict
    # Enf of getUserInfo


# --------------------------------------------------------------------
#
# doPull
#
# --------------------------------------------------------------------
def doPull(pDict):
    """
    Args:
    Returns:
    """
    RS = pDict['RS']
    rDict = bbblib.genReturnDict('Inside doPull')
    
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
            # End of else
        # End of else
    except (ConnectionError) as e:
        BP = 0

    pDict['Blocks']     = jObj['blocks']
    pDict['latestDate'] = jObj['date']
        
    return rDict
    # End of doPull


# --------------------------------------------------------------------
#
# listCategories
#
# --------------------------------------------------------------------
def listCategories(pDict):
    """
    Args:
    Returns:
    """
    RS = pDict['RS']
    rDict = bbblib.genReturnDict('Inside doCheck')
    
    blockNames = pDict['BlockNames']
    print("\nDefined block categories")
    for entry in blockNames:
        print(f"    {entry}")
    print("\n")

    rDict['status'] = RS.CALL_EXIT
    rDict['msg'] = 'Call exit'
    
    return rDict
    # End of listCategories


# --------------------------------------------------------------------
#
# doCheck
#
# --------------------------------------------------------------------
def doCheck(pDict):
    """
    Args:
    Returns:
    """
    RS = pDict['RS']
    rDict = bbblib.genReturnDict('Inside doCheck')

    if pDict['BSLib'] == RS.NO:
        from atproto import Client, models
        from atproto.exceptions import BadRequestError
        pDict['BSLib_loaded'] = RS.YES
    
    blueSkyLogin  = pDict['blueSkyLogin']
    blueSkyPasswd = pDict['blueSkyPasswd']
        
    client = Client()
    client.login(blueSkyLogin, blueSkyPasswd)

    # TEST
    #a1 = client.app
    #a2 = client.app.bsky
    #a3 = client.app.bsky.graph
    #a4  = client.app.bsky.graph.block

    # AppBskyGraphBlockRecord
        
    #for entry in a4:
    #    BP = 0

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
            B3 = bbblib.defineB3(UD)
            foundList.append(name)
            if args.debug:
                print(f"Account: {name} found")
            # End of for loop
            BP = 1
        BP = 2
    BP = 3
    return rDict
    # End of doCheck

# --------------------------------------------------------------------
#
# backupDB
#
# --------------------------------------------------------------------
def backupDB(pDict):
    RS = pDict['RS']
    rDict = bbblib.genReturnDict('Inside doCheck')

    rDict['status'] = RS.CALL_EXIT
    
    return rDict

# --------------------------------------------------------------------
#
# printVersion
#
# --------------------------------------------------------------------
def printVersion(pDict):
    RS = pDict['RS']
    rDict = bbblib.genReturnDict('Inside doCheck')

    toolName = pDict['toolName']
    version  = pDict['version']

    print(f"{toolName} - Version: {version}")
    
    rDict['status'] = RS.CALL_EXIT
    
    return rDict
    #
    
# --------------------------------------------------------------------
#
# entry point
#
# --------------------------------------------------------------------
if __name__ == '__main__':
    main()
