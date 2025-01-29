#!/usr/bin/env python3
# -*- mode: python -*-
# -*- coding: utf-8 -*-

import os, sys
import pprint
import json
#import requests
#import argparse
#import toml
#import sqlite3 as S3
#import hashlib
#import datetime

from atproto import Client, models
from atproto.exceptions import BadRequestError
from atproto_client.models.app.bsky.graph import get_lists
from atproto import models

def main():
    blueSkyLogin  = os.environ.get('blueSkyLogin', '')
    blueSkyPasswd = os.environ.get('blueSkyPasswd', '')

    client = Client()
    client.login(blueSkyLogin, blueSkyPasswd)

    # UD - User Data
    UD = client.me

    ME = defineME(UD)

    DID = ME['did']

    #data = client.get_profile(actor='did:plc:...')
    data = client.get_profile(actor=DID)
    did = data.did
    display_name = data.display_name

    # atproto_client/models/app/bsky/graph/get_lists

    # w = client.get_lists(actor=DID)
    #w = models.app.bsky.graph.get_list(actor=DID)
    #l = get_lists(actor=DID)

    blockedUser = 'hhcst67.bsky.social'
    data = client.get_profile(actor='hhcst67.bsky.social')
    blockedUserDID = data.did
    ME2 =  defineME(data)
    #pprint.pprint(ME2)
    jStr = json.dumps(data, indent=4)
    print(jStr)
    
    block_record = models.AppBskyGraphBlock.Record(
        subject=blockedUserDID, 
        created_at=client.get_current_time_iso()
        )
    uri = client.app.bsky.graph.block.create(client.me.did, block_record).uri

    sys.exit(0)
    #

def defineME(rDict: dict) -> dict:
    ME = {}

    for entry in rDict:
        if isinstance(entry, tuple):
            key   = entry[0]
            value = entry[1]
            ME[key] = value
        else:
            continue

    return ME
    #
    
if __name__ == '__main__':
    main()
