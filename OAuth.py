#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Handles our initial oauth request."""
from mixer_shortcode import OAuthClient, ShortCodeAccessDeniedError,\
    ShortCodeTimeoutError
from subprocess import Popen
import asyncio
import json
import os
import sys


try:
    my_client_id = os.environ['Client_ID']
    my_client_secret = os.environ['Client_Secret']
    print(my_client_id)
    print(my_client_secret)
except KeyError:
    print("Please set the environment variables Client_ID and Client_Secret")
    sys.exit(1)
scopes = ["channel:details:self channel:update:self chat:bypass_catbot "
          "chat:bypass_filter chat:bypass_slowchat chat:change_ban "
          "chat:change_role chat:chat chat:clear_messages chat:connect "
          "chat:poll_start chat:purge chat:remove_message chat:timeout "
          "chat:whisper"]


def out(access_token, token_type, token_expires_at, refresh_token):
    """Write tokens to a file."""
    data = []
    print(token_expires_at)
    token_expires_at = "".join(str(
        token_expires_at).split(".")[0])
    data.append({"access_token": access_token, "token_type": token_type,
                "expires_in": token_expires_at, "refresh_token":
                    refresh_token})
    with open("tokens", "w") as outfile:
        json.dump(data, outfile)


async def get_access_token(client):
    """Open Firefox to get user to approve our shortcode request."""
    code = await client.get_code()
    print("Go to mixer.com/go and enter {}".format(code.code))
    p = Popen(["firefox", "https://mixer.com/go?code={}".format(
               code.code)])
    try:
        OaTokens = await code.accepted()
        p.terminate()
        return OaTokens
    except ShortCodeAccessDeniedError:
        print("The user denied access to our client")
    except ShortCodeTimeoutError:
        print("Yo, you're too slow! Let's try again...")
        return await get_access_token(client)


async def run():
    """Await loop for our main code."""
    async with OAuthClient(my_client_id, scopes=scopes,
                           client_secret=my_client_secret) as client:
        token = await get_access_token(client)
        print("Access token: {}".format(token.access))
        print("Refresh token: {}".format(token.refresh))
        print("Exipres at: {}".format("".join(str(
            token.expires_at).split(".")[0])))
        out(token.access, "Bearer", token.expires_at, token.refresh)
asyncio.get_event_loop().run_until_complete(run())
