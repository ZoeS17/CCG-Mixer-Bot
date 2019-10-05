#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Config File """

import json
import os
import requests
import sys
from datetime import *

# DO NOT CHANGE THESE VALUES OR THE BOT WILL BREAK
Mixer_URI = 'https://mixer.com/api/v1/'
USERSCURRENT_URI = 'users/current'
CHATSCID_URI = 'chats/{cid}'
CHANNEL_NAME = sys.argv[1]
ACCESS_TOKEN = ""
REFRESH_TOKEN = ""
EXPIRES_AT = ""

# THE SETTINGS BELOW CAN BE CHANGED
# Client ID, obtained from https://beam.pro/lab
# select OAUTH CLIENTS and copy ID
# ACCESS_TOKEN = OAuth.my_token
def loadTokens():
    global ACCESS_TOKEN
    global REFRESH_TOKEN
    global EXPIRES_AT
    with open('tokens') as json_file:
        data = json.load(json_file)
        for k in data:
            ACCESS_TOKEN = k['access_token']
            REFRESH_TOKEN = k['refresh_token']
            EXPIRES_AT = k['expires_in']
loadTokens()
if datetime.fromisoformat(EXPIRES_AT) < datetime.now():
    import OAuth
    loadTokens()
try:
    CLIENTID = os.environ['Client_ID']
except KeyError:
    print("Please set the environment variable Client_ID")
    sys.exit(1)


# This gets the ID for the channel you wish to join
s = requests.Session()
s.headers.update({'Client-ID': CLIENTID})
channel_response = s.get(f'https://mixer.com/api/v1/channels/{CHANNEL_NAME}')
CHANNELID = channel_response.json()['id']

# This is up to you to obtain. This can be done though
# Rest API. for more info https://dev.beam.pro/reference/oauth/index.html


# enables/disables raw chat details as recieved from the server
# without the chat formatting
if len(sys.argv) > 3:
    if (sys.argv[3] != ''):
        ACCESS_TOKEN = sys.argv[3]
    else:
        print("Nice try! Get an access token fool!")
        sys.exit(1)
elif len(sys.argv) > 2:
    if sys.argv[2].lower() == "true":
        CHATDEBUG = True
    else:
        CHATDEBUG = False
else:
    CHATDEBUG = False
