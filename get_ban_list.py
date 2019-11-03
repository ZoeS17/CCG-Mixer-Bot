#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Get the ban list from the selected channel via the mixer API."""
import requests
import sys
import os


def getBanList(remote=""):
    try:
        my_client_id = os.environ['Client_ID']
    except KeyError:
        print("Please set the environment varrible Client_ID")
        sys.exit(1)
    if remote == "":
        if len(sys.argv) > 1:
            channelName = sys.argv[1]
        else:
            print(f"[USAGE]: {sys.argv[0]} <channel name>")
            sys.exit(2)

        # This gets the ID for the channel you wish to join
    else:
        channelName = remote
    s = requests.Session()
    s.headers.update({'Client-ID': my_client_id})
    channel_response = s.get(
        f"https://mixer.com/api/v1/channels/{channelName}")
    CHANNELID = channel_response.json()["id"]
    bans_response = s.get(
        f"https://mixer.com/api/v1/channels/{CHANNELID}"
        "/users/Banned?fields=username&limit=100&page=0")
    os.remove(f"./logs/{channelName}/banList")
    # Check if pagnation is required.
    bans_count = int(bans_response.headers['x-total-count'])
    if(bans_count > 100):
        pages = int(bans_count / 100)
        bans_response = bans_response.json()
        data = {x['username'] for x in bans_response}
        banList = list(data)
        with open(f"./logs/{channelName}/banList", "w", encoding='utf-8') as f:
            for item in banList:
                f.write(item + "\n")
        for i in range(1, pages):
            bans_response = s.get(
                f"https://mixer.com/api/v1/channels/{CHANNELID}"
                f"/users/Banned?fields=username&limit=100&page={i}")
            bans_response = bans_response.json()
            data = {x['username'] for x in bans_response}
            banList = list(data)
            with open(f"./logs/{channelName}/banList",
                      "a", encoding='utf-8') as f:
                for item in banList:
                    f.write(item + "\n")
    else:
        bans_response = s.get(
            f"https://mixer.com/api/v1/channels/{CHANNELID}"
            f"/users/Banned?fields=username&limit=100")
        bans_response = bans_response.json()
        data = {x['username'] for x in bans_response}
        banList = list(data)
        with open(f"./logs/{channelName}/banList",
                  "w", encoding='utf-8') as f:
            for item in banList:
                f.write(item + "\n")
    os.system(f"sort ./logs/{channelName}/banList -o "
              f"./logs/{channelName}/banList")


if __name__ == "__main__":
    getBanList()
