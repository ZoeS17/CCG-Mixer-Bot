#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Handles and formats chat events. """
import csv
import json
import os
import re
import requests
import sys
from datetime import *
from pwnlib.term import text
from setproctitle import setproctitle
from User import User


class Logger:

    def __init__(self, stdout):
        global CHATDEBUG
        today = date.today()
        print(today)
        if CHATDEBUG is True:
            self.filename = f"./logs/{channelName}/Debug/{today}.mlog"
        else:
            self.filename = f"./logs/{channelName}/{today}.mlog"
        self.stdout = stdout
        self.logfile = open(self.filename, "a", buffering=1)

    def __getattr__(self, attr):
        return getattr(self.stdout, attr)

    def close(self):
        self.logfile.close()

    def flush(self):
        self.logfile.flush()

    def write(self, text):
        self.logfile.write(text)
        self.logfile.flush()


class _debug:
    def __init__(self, msg):
        sys.__stdout__.write(str(msg) + "\n")
        sys.__stdout__.flush()

class _print:
    def __init__(self, msg, color=None):
        self.color = color
        red = text.red
        yellow = text.yellow
        green = text.green
        print(msg)
        if self.color == "red":
            sys.__stdout__.write(red(msg) + "\a\n")
            sys.__stdout__.flush()
        elif self.color == "yellow":
            sys.__stdout__.write(yellow(msg) + "\n")
            sys.__stdout__.flush()
        elif self.color == "green":
            sys.__stdout__.write(green(msg) + "\n")
            sys.__stdout__.flush()
        else:
            sys.__stdout__.write(msg + "\n")
            sys.__stdout__.flush()


channelName = sys.argv[1]
if len(sys.argv) > 1:
    if sys.argv[2].lower() == "true":
        CHATDEBUG = True
    else:
        CHATDEBUG = False

log = Logger(sys.stdout)
sys.stdout = log
sys.__stdout__.flush()
awayAdmins = list()
users = {}


class Tokens:
    """Tokens is a bearer from an OAuth access and refresh token retrieved
    via the :func:`~interactive_python.Handler.refresh` method.
    """

    def __init__(self, body):
        self.access = body['access_token']
        self.refresh = body['refresh_token']
        self.expires_at = datetime.now() +\
            timedelta(seconds=body['expires_in'])


class Handler():
    """Handles chat events."""

    def __init__(self, config, chat):
        self.config = config
        self.event_types = {
            "reply": self.type_reply, "event": self.type_event,
            "method": self.type_method, "system": self.type_system}
        self.poll_switch = True
        self.chat = chat
        self.warns = ""
        self.warnList = []
        self.warnListIDs = []
        self.username = ""
        setproctitle(f"Mixer[{channelName}]")

    def isAdmin(self, un):
        un = un.lower()
        with open(f"./Admins", "rt", encoding='utf-8') as a:
            lines = a.read().splitlines()
            if un in lines:
                return True
            else:
                return False

    def top_role(self, roles):
        if "Banned" in roles:
            return "Banned"
        elif "Owner" in roles:
            return "Owner"
        elif "Mod" in roles:
            return "Mod"
        elif "ChannelEditor" in roles:
            return "Editor"
        elif "Founder" in roles:
            # see note in Global Mod
            return "Founder"
        elif "Staff" in roles:
            # see note in Global Mod
            return "Staff"
        elif "GlobalMod" in roles:
            """
            Change to the following to reassign Global Mods inside this logger
            "User" - Ignore all Mod+ commands
            "Mod" - Ignore all Owner+ commands
            """
            return "GlobalMod"
        elif "Pro" in roles:
            return "Pro"
        else:
            return "User"

    def refresh(self, invoker):
        try:
            my_client_id = os.environ['Client_ID']
            my_client_secret = os.environ['Client_Secret']
        except KeyError:
            pass
        with open('tokens', "r") as json_file:
            data = json.load(json_file)
            for k in data:
                REFRESH_TOKEN = k['refresh_token']
                expires_at = k['expires_in']
        if datetime.fromisoformat(expires_at) < datetime.now():
            rs = requests.Session()
            rjson = {"client_id": my_client_id, "client_secret":
                     my_client_secret, "refresh_token": REFRESH_TOKEN,
                     "grant_type": "refresh_token"}
            with rs.post(url="https://mixer.com/api/v1/oauth/token",
                         json=rjson) as resp:
                newTokens = Tokens(resp.json())
            newTokens.expires_at = "".join(str(newTokens.expires_at
                                               ).split(".")[0])
            self.config.ACCESS_TOKEN = newTokens.access
            self.config.REFRESH_TOKEN = newTokens.refresh
            self.config.EXPIRES_AT = newTokens.expires_at
            self.chat.whisper(invoker, "OAuth token now expire at: "
                              f"{newTokens.expires_at}")
            with open('tokens', 'w') as token_file:
                tokenOut = []
                token_type = "Bearer"
                tokenOut.append({"access_token": newTokens.access,
                                 "token_type": token_type, "expires_in":
                                 newTokens.expires_at, "refresh_token":
                                 newTokens.refresh})
                json.dump(tokenOut, token_file)

    def adminCmd(self, adm, params):
        d = params.split(" ")
        cmd = d[0].lower()
        warn = "yellow"
        bad = "red"
        good = "green"
        if len(d) > 1:
            aparam = d[1].lower()

        if cmd == "add":
            with open(f"./Admins", "at", encoding='utf-8') as f:
                f.write(d[1].lower() + "\n")
            msg = f"Added user {aparam} to the admin list."
            self.chat.whisper(adm, msg + "\n")

        elif cmd == "del":
            with open(f"./Admins", "rt", encoding='utf-8') as o:
                with open(f"./.tmp_Admins", "wt", encoding='utf-8') as n:
                    lines = o.read().splitlines()
                    for item in lines:
                        if item == d[1].lower():
                            pass
                        else:
                            n.write(item + "\n")
            os.remove("./Admins")
            os.rename("./.tmp_Admins", "./Admins")
            msg = f"Deleted user {aparam} from the admin list."
            self.chat.whisper(adm, msg + "\n")

        elif cmd == "list":
            msg = ""
            with open(f"./Admins", "rt", encoding='utf-8') as f:
                lines = f.read().splitlines()
                msg += " ".join(lines)
                self.chat.whisper(adm, msg + "\n")
        elif cmd == "away":
            global awayAdmins
            adm = adm.lower()
            if adm in awayAdmins:
                awayAdmins.remove(adm)
                self.chat.whisper(adm, "You have returned from away.")
            else:
                awayAdmins.append(adm)
                self.chat.whisper(adm, "You have been marked away.")
        elif cmd == "refresh":
            self.refresh(adm)
        # new commands here
        # elif cmd == "":
        # pass

    def warnUpdate(self):
        with open(f"./logs/{channelName}/warnings", "rt",
                  encoding="utf-8", newline="") as f:
            warnreader = csv.DictReader(f, dialect="excel-tab")
            for row in warnreader:
                self.warnList.append(row["Name"])
                self.warnListIDs.append(row["uid"])

    def _json_object_hook(self, d):
        global users
        d["admin"] = self.isAdmin(d["username"])
        d["mod"] = False
        d["toprole"] = self.top_role(d["userRoles"])
        d.pop("userRoles")
        for k,v in d.items():
            if k == "toprole":
                if v == "Mod":
                    d["mod"] = True
        users[d["username"]] = repr(User(**d))

    def json2obj(self, data):
        json.loads(data, object_hook=self._json_object_hook)

    def chatusers(self):
        global users
        cs = requests.Session()
        cs.headers.update({'Client-ID': os.environ['Client_ID']})
        ChannelId = self.config.CHANNELID
        chats_resp = cs.get(f"https://mixer.com/api/v2/chats/{ChannelId}/users")
        self.json2obj(chats_resp.text)


    def command(self, cmd, data, params, role):
        invoker = data["data"]["user_name"]
        warn = "yellow"
        bad = "red"
        good = "green"
        if cmd.startswith("admin"):
            """ We can't delete a whisper so don't try. """
            if "whisper" in data["data"]["message"]["meta"]:
                pass
            else:
                self.chat.delete_msg(data["data"]["id"])
            """ Invoke admin command handler if appropriate. """
            if self.isAdmin(invoker):
                self.adminCmd(invoker, params)
            else:
                self.chat.whisper(invoker,
                                  "You must be an admin of the bot"
                                  " to use that command.")
        elif cmd.startswith("warn"):
            if "whisper" in data["data"]["message"]["meta"]:
                pass
            else:
                self.chat.delete_msg(data["data"]["id"])
            if ((role == "Mod") or (role == "Owner")):
                """ Write warning to channel/warnings file. """
                warnings = f"./logs/{channelName}/warnings"
                o = params.split(" ")
                user = o[0]
                user = re.split("@", user)[1]
                wSess = requests.Session()
                wSess.headers.update({'Client-ID': os.environ['Client_ID']})
                wid = wSess.get(f"https://mixer.com/api/v1/channels/{user}"
                                "?fields=userId").json()["userId"]
                mesg = " ".join(o[1:])
                warning = f"{user}\t{wid}\t{mesg}"
                with open(warnings, "a") as warn:
                    warn.write(f"{warning}\n")
                _print(f"{invoker} warned user {user} \"{mesg}\"", color=warn)
                self.warnUpdate()
                self.chat.purge(user)
                self.chat.whisper(user, mesg)
        elif cmd.startswith("banlist"):
            if "whisper" in data["data"]["message"]["meta"]:
                postCount = False
            else:
                self.chat.delete_msg(data["data"]["id"])
                postCount = True
            if ((role == "Mod") or (role == "Owner")):
                """Write bans to channel/banList file."""
                from get_ban_list import getBanList
                getBanList(remote=f"{channelName}")
                count = os.popen("echo $(wc -l ./logs/"
                                 f"{channelName}/banList)|awk '"
                                 "{print $1}'").read()[:-1]
                if postCount:
                    self.chat.message(f"{count} trolls")
                else:
                    self.chat.whisper(invoker, f"{count} trolls")

                # TODO: Figure out Discord Webhooks
                # webhookURL = ("")
                # WebhookFile = f"{channelName} - Ban List.txt"
                # staging = '{"content": "Bans", "tts": false, "embed": { "title"'
                # staging = staging + ': "'+ WebhookFile + '"} }'
                # payload = json.loads(staging)
                # sys.__stdout__.write(staging + "\n" + str(payload) + "\n")
                # sys.__stdout__.flush()
                # d = requests.Session()
                # d.headers.update({'Content-Type': 'multipart/form-data',
                #                   'Content-Disposition': WebhookFile})
                # with open("/root/code/CourtesyCallBot/Mixer/logs/"
                #           f"{channelName}/banList", "rb") as Dfile:
                #     payload = {'content': f"{channelName} - Ban List",
                #                'tts': False}
                #     form = aiohttp.FormData()
                #     form.add_field("payload_json",payload)
                #     form.add_field("file", Dfile, filename=WebhookFile,
                #                     content_type="application/octet-stream")
                #     (filename, fileobj, contentype)
                #     fileStage = (WebhookFile, Dfile, 'application/octet-stream')
                #     sys.__stdout__.write(repr(fileStage) + "\n")
                #     sys.__stdout__.flush()
                #     files = {'file': fileStage}
                #     disco = d.post(webhookURL, data=payload, files=files)
                #     sys.__stdout__.write(disco.text + "\n")
                #     sys.__stdout__.flush()

        # new commands here
        # elif cmd.startswith(""):
            # pass

    def formatting(self, data):
        """ Check the event type and calls the function for that type. """
        func = self.event_types[data["type"]]
        func(data)
        if self.config.CHATDEBUG:
            _print(data)

    def type_reply(self, data):
        """ Handle the Reply type data. """
        try:
            # Deal with an edge case where whispers sometimes cause a TypeError.
            if "data" in data:
                _debug("[Data]"+repr(data))
                if type(data["data"]) is not str:
                    if "authenticated" in data["data"]:
                        if data["data"]["authenticated"]:
                            self.username = self.chat.username
                            os.system("clear")
                        else:
                            _print("Authenticated Failed, Chat log restricted")
                    elif "whisper" in data["data"]["message"]["meta"]:
                        pass
                    else:
                        pass
                elif "Message deleted." in data["data"]:
                    pass
            else:
                _debug(f"Server Reply[error]: {data['error']}")
        except TypeError as e:
            _debug("Data: "+repr(data))

    def type_event(self, data):
        """ Handle the reply chat event types. """
        global awayAdmins
        global users
        warn = "yellow"
        bad = "red"
        good = "green"
        s = requests.Session()
        s.headers.update({'Client-ID': os.environ['Client_ID']})
        event_string = {
            "UserJoin": "{} has joined the channel.",
            "UserLeave": "{} has left the channel.",
            "ChatMessage": "{user}: {msg}",
            "whisper": "{user} → {target} : {msg}",
            "me": "{user} {msg}",
            "PollStart": "{} has started a poll.",
            "PollEnd": "The poll started by {} has ended.",
            "ClearMessages": "{} has cleared chat.",
            "UserUpdate": "{username}'s top role is now {role}.",
            "Ban": "{username}'s was {role}.",
            "PurgeMessage": "{modname} has purged {username}'s messages.",
            "SkillAttribution": "{user} used the {skill} skill for {sparks}.",
            "DeleteMessage": "{Mod} deleted a message."}

        if data["event"] == "WelcomeEvent":
            self.warnUpdate()
            self.chatusers()

        elif data["event"] == "UserUpdate":
            users_resp = s.get("https://mixer.com/api/v1/users/{}".format(
                data["data"]["user"]))
            users_resp = users_resp.json()["username"]
            test = data["data"]["roles"]
            role = self.top_role(test)
            _print(event_string[data["event"]].format(
                   username=users_resp,
                   role=role), color=warn)

        elif data["event"] == "UserJoin" or data["event"] == "UserLeave":
            if data["data"]["username"] is not None:
                usr = data["data"]["username"]
                usrid = data["data"]["id"]
                _print(event_string[data["event"]].format(
                    usr))
                if data["event"] == "UserJoin":
                    roles = data["data"]["roles"]
                    if "Mod" in roles:
                        if self.isAdmin(usr) is True:
                            users[usr] = User(username=usr, userId=usrid,
                                              toprole="Mod", admin=True)
                        else:
                            users[usr] = User(username=usr, userId=usrid,
                                              toprole="Mod", admin=False)
                    else:
                        users[usr] = User(username=usr, userId=usrid,
                                             toprole=self.top_role(roles),
                                             admin=False)
                else:
                    self.chat.whisper(self.username,
                                      f"{usr} has left the channel.")
                    if usr in users:
                        users.pop(usr)

        elif data["event"] == "PurgeMessage":

            users_response = s.get("https://mixer.com/api/v1/users/{}".format(
                data["data"]["user_id"])).json()["username"]
            USERNAME = users_response

            if "moderator" in data["data"]:

                mod = data["data"]["moderator"]["user_name"]
                _print(f"{mod} has purged {USERNAME}'s messages.", color=warn)

            else:

                users_reply = s.get("https://mixer.com/api/v1/users/{}".format(
                                    data["data"]["user_id"]))
                users_reply = users_reply.json()["username"]
                _print(event_string["Ban"].format(
                           username=users_reply,
                           role="Banned"
                           ),
                       color=bad)

        elif data["event"] == "DeleteMessage":
            _print(event_string[data["event"]].format(
                Mod=data["data"]["moderator"]["user_name"]),
                color=warn)

        elif data["event"] == "ClearMessages":
            _print(event_string[data["event"]].format(
                data["data"]["clearer"]["user_name"]))

        elif data["event"] == "PollStart":
            if self.poll_switch:
                _print(event_string[data["event"]].format(
                    data["data"]["author"]["user_name"]))
                self.poll_switch = False

        elif data["event"] == "PollEnd":
            _print(event_string[data["event"]].format(
                data["data"]["author"]["user_name"]))
            self.poll_switch = True

        elif data["event"] == "SkillAttribution":
            user = data["data"]["user_name"]
            skill = data["data"]["skill"]["skill_name"]
            sparks = data["data"]["skill"]["cost"]
            _print(event_string["SkillAttribution"].format(
                user=user,
                skill=skill,
                sparks=sparks))

        elif data["event"] == "ChatMessage":
            msg = "".join(
                item["text"] for item in data["data"]["message"]["message"])
            if msg.startswith("~"):
                msg = "".join(msg.split("~")[1])
                cmd = "".join(msg.split(" ")[0]).lower()
                param = " ".join(msg.split(" ")[1:])
                role = self.top_role(data["data"]["user_roles"])
                self.command(cmd, data, param, role)
            elif "whisper" in data["data"]["message"]["meta"]:
                user = data["data"]["user_name"]
                target = data["data"]["target"]
                if target.lower() in awayAdmins:
                    z = self.username.lower()
                    if user.lower() == z and target.lower() == z:
                        pass
                    else:
                        self.chat.whisper(user, f"{target} is away.")
                if target.lower() == self.username.lower():
                    _debug(f"{user} → {target} : {msg}")

            elif "me" in data["data"]["message"]["meta"]:
                _print(event_string["me"].format(
                    user=data["data"]["user_name"],
                    msg=msg))
            else:
                user = data["data"]["user_name"]
                userID = str(data["data"]["user_id"])
                if userID in self.warnListIDs:
                    _print(event_string[data["event"]].format(
                               user=user,
                               msg=msg),
                           color=warn)
                    self.chat.whisper(self.username,
                                      f"@{self.username} [WARN] " + user)
                else:
                    _print(event_string[data["event"]].format(
                        user=user,
                        msg=msg))
                if msg.startswith("We're now hosting @"):
                    _print("-" * 80)
                    self.chat.whisper("Scottybot", "!queue purge")
                    self.chat.whisper("Scottybot", "!set queue off")
                    self.chat.clear_chat()
        else:
            _debug(f"[debug] {data}")

    def type_method(self, data):
        """ Handle the reply chat event types. """
        if self.config.CHATDEBUG:
            if data["method"] == "auth":
                pass
            elif data["method"] == "msg":
                if self.config.CHATDEBUG:
                    _debug(f"METHOD MSG: {data}")
            else:
                _debug(f"METHOD MSG:  {data}")

    def type_system(self, data):
        """ Handle the reply chat event types. """
        if self.config.CHATDEBUG:
            _debug(f"SYSTEM MSG:  {data['data']}")
