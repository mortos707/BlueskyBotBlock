
#!/usr/bin/env python3

# B3 - BlueSky Bot Block

import os, sys
import json
import requests
import sqlite3 as S3
from atproto import Client, models
from atproto.exceptions import BadRequestError


# --------------------------------------------------------------------
#
# main
#
# --------------------------------------------------------------------
def main():
    baseDir = os.environ['PWD']

    pDict = {}
    
    pDict['inLink']    = 'https://redwoodempire.org/B3/latest.json'
    pDict['baseDir']   = os.environ['PWD']
    pDict['B3DB']      = f"{pDict['baseDir']}/../data/B3.sqlite"
    pDict['S3']        = S3
    pDict['tableName'] = 'B3'

    blueSkyLogin  = os.environ['blueSkyLogin']
    blueSkyPasswd = os.environ['blueSkyPasswd']

    debug   = False
    doCheck = False
    doPull  = True
    
    notFoundList = []
    foundList    = []
    jObj = ''

    if doPull:
        try:
            r = requests.get(pDict['inLink'])
            if r.status_code != 200:
                print(f"Error: {inLink} not found")
                sys.exit(1)
            else:
                jObj = r.json()
                pDict['jObj'] = jObj
        except (ConnectionError) as e:
        BP = 0

        Blocks = jObj['blocks']
        loadDB(pDict)

    if doCheck:
        client = Client()
        client.login(blueSkyLogin, blueSkyPasswd)

    for key in Blocks:
        BL = Blocks[key]
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
                    if debug:
                        print(f"Account: {name} NOT found")
                    continue
            BP = 0
            ME = defineME(UD)
            foundList.append(name)
            if debug:
                print(f"Account: {name} found")
            # End of for loop
        BP = 1

    notFoundCount = len(notFoundList)
    foundCount    = len(foundList)
    accountTotal = notFoundCount + foundCount
    
    sys.exit(0)
    # End of main

# --------------------------------------------------------------------
#
# defineME
#
# --------------------------------------------------------------------
def defineME(me):
    ME = {}
    for entry in me:
        key   = entry[0]
        value = entry[1]
        ME[key] = value
        
    return ME
    #

def defineB3(res):

    return defineME(res)
    # End of defineB3
    
# --------------------------------------------------------------------
#
# loadDB
#
# --------------------------------------------------------------------
def loadDB(pDict):
    jObj      = pDict['jObj']
    dbFile    = pDict['B3DB']
    S3        = pDict['S3']
    tableName = pDict['tableName']
    
    """
    CREATE TABLE IF NOT EXISTS "B3" (
	"rec_num"	INTEGER,
	"name"	TEXT,
	"status"	TEXT,
	"block"	TEXT,
	"active"	TEXT,
	"group"	TEXT,
	PRIMARY KEY("rec_num" AUTOINCREMENT)
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
                ' "rec_num"       INTEGER, '
                ' "name"          TEXT, '
                ' "status"        TEXT, '
                ' "block"         TEXT, '
                ' "active"        TEXT, '
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
        BL = Blocks[key]
        for entry in BL:
            name = entry.strip()
            if '@' in name:
                name = name.replace('@', '')
            query2 = f" select * from {tableName} where name = \'{name}\';"
            handle = cur.execute(query2).fetchall()
            if handle == []:
                # user not found
                BP = 5
            else:
                Bp = 6
                B3 = defineB3(handle)
            BP = 2
        BP = 3
    BP = 4

    return
    #
    
# --------------------------------------------------------------------
#
# entry point
#
# --------------------------------------------------------------------
if __name__ == '__main__':
    main()
