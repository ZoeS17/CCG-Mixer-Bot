#! /usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test refresh stuffs"""

import datetime
import json
import os
import sys

try:
    my_client_id = os.environ['Client_ID']
    my_client_secret = os.environ['Client_Secret']
    print(my_client_id)
    print(my_client_secret)
except KeyError:
    print("Please set the environment varribles Client_ID and Client_Secret")
    sys.exit(1)
with open('tokens') as json_file:
    data = json.load(json_file)
    for k in data:
        ACCESS_TOKEN = k['access_token']
        REFRESH_TOKEN = k['refresh_token']
        EXPIRES_AT = k['expires_in']
expiry_time = datetime.datetime.fromisoformat(EXPIRES_AT)
time_now = datetime.datetime.now()
print(expiry_time)
print(time_now)
difference = time_now - expiry_time
print(difference)
