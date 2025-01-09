#!/usr/bin/env python3

# B3 - BlueSky Bot Block

import os, sys
import json
from atproto import Client, models
from atproto.exceptions import BadRequestError

def main():
    baseDir = '/usr3/home/jgrosch/Git/Lorax/Data'
    inFile  = f"{baseDir}/MagaBlockList.07-Jan-2025.json"
    debug   = False
    
    notFoundList = []
    foundList    = []

    blueSkyLogin  = os.environ['blueSkyLogin']
    blueSkyPasswd = os.environ['blueSkyPasswd']

    client = Client()
    client.login(blueSkyLogin, blueSkyPasswd)

    with open(inFile, 'r') as fh:
        xLines = fh.read()

    jObj = json.loads(xLines)
    Accounts = jObj['accounts']

    for entry in Accounts:
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

def defineME(me):
    ME = {}
    for entry in me:
        key   = entry[0]
        value = entry[1]
        ME[key] = value
        
    return ME
    #
if __name__ == '__main__':
    main()
