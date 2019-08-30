#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Handles and formats chat events. """
import json
import os
import sys
import requests
from datetime import *


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
        self.stdout.write(text)
        self.logfile.write(text)
        self.logfile.flush()


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
    """ Handles chat events. """
    def __init__(self, config, chat):
        self.config = config
        self.event_types = {
            "reply": self.type_reply, "event": self.type_event,
            "method": self.type_method, "system": self.type_system}
        self.poll_switch = True
        self.chat = chat

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
            self.chat.whisper(invoker, "OAuth token now expires at: "
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

    def command(self, cmd, data, params, role):
        invoker = data["data"]["user_name"]
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
                mesg = " ".join(o[1:])
                warning = f"{user}\t{mesg}"
                with open(warnings, "a") as warn:
                    warn.write(f"{warning}\n")
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
                count = os.popen("echo $(wc -l /root/code/CourtesyCallBot/"
                                 f"Mixer/logs/{channelName}/banList)|awk '"
                                 "{print $1}'").read()[:-1]
                if postCount:
                    self.chat.message(f"{count} trolls")
                else:
                    self.chat.whisper(invoker, f"{count} trolls")
        # new commands here
        # elif cmd.startswith(""):
            # pass

    def formatting(self, data):
        """ Check the event type and calls the function for that type. """
        func = self.event_types[data["type"]]
        func(data)
        if self.config.CHATDEBUG:
            print(data)

    def type_reply(self, data):
        """ Handle the Reply type data. """
        if "data" in data:
            if "authenticated" in data["data"]:
                if data["data"]["authenticated"]:
                    os.system("clear")
                    # print("Authenticated with the server")
                    pass
                else:
                    print("Authenticated Failed, Chat log restricted")
            elif "Message deleted." in data["data"]:
                pass
            elif "whisper" in data["data"]["message"]["meta"]:
                pass
            else:
                pass
        else:
            sys.__stdout__.write(f"Server Reply[error]: {data['error']}\n")
            sys.__stdout__.flush()

    def type_event(self, data):
        """ Handle the reply chat event types. """
        global awayAdmins
        s = requests.Session()
        s.headers.update({'Client-ID': os.environ['Client_ID']})
        event_string = {
            "WelcomeEvent": "Connected to the channel chat...",
            "UserJoin": "{} has joined the channel.",
            "UserLeave": "{} has left the channel.",
            "ChatMessage": "{user}: {msg}",
            "whisper": "{user} → {target} : {msg}",
            "me": "{user} {msg}",
            "PollStart": "{} has started a poll.",
            "PollEnd": "The poll started by {} has ended.",
            "ClearMessages": "{} has cleared chat.",
            "UserTimeout": "{userName} has been timed out for {length} mins.",
            "UserUpdate": "{username}'s top role is now {role}.",
            "PurgeMessage": "{modname} has purged {username}'s messages.",
            "SkillAttribution": "{user} used the {skill} skill for {sparks}.",
            "DeleteMessage": "{Mod} deleted a message."}

        if data["event"] == "WelcomeEvent":
            # print(event_string[data["event"]])
            pass

        elif data["event"] == "UserTimeout":
            timeLen = data["data"]["duration"]
            print(event_string[data["event"]].format(
                userName=data["data"]["user"]["user_name"],
                length=round(timeLen / 60000)))
            print(f"[DEBUG - UserTimeout] {data}")

        elif data["event"] == "UserUpdate":
            users_resp = s.get("https://mixer.com/api/v1/users/{}".format(
                data["data"]["user"])).json()["username"]
            test = data["data"]["roles"]
            role = self.top_role(test)
            print(event_string[data["event"]].format(
                  username=users_resp,
                  role=role
                  ))

        elif data["event"] == "UserJoin" or data["event"] == "UserLeave":
            if data["data"]["username"] is not None:
                usr = data["data"]["username"]
                print(event_string[data["event"]].format(
                    usr))
                if data["event"] == "UserJoin":
                    pass
                else:
                    self.chat.whisper("Zoe_S17",
                                      f"{usr} has left the channel.")

        elif data["event"] == "PurgeMessage":
            users_response = s.get("https://mixer.com/api/v1/users/{}".format(
                data["data"]["user_id"])).json()["username"]
            USERNAME = users_response
            if "moderator" in data["data"]:
                mod = data["data"]["moderator"]["user_name"]
                print(f"{mod} has purged {USERNAME}'s messages.")
            else:
                pass

        elif data["event"] == "DeleteMessage":
            # pass
            print(event_string[data["event"]].format(
                Mod=data["data"]["moderator"]["user_name"]))

        elif data["event"] == "ClearMessages":
            print(event_string[data["event"]].format(
                data["data"]["clearer"]["user_name"]))

        elif data["event"] == "PollStart":
            if self.poll_switch:
                print(event_string[data["event"]].format(
                    data["data"]["author"]["user_name"]))
                self.poll_switch = False

        elif data["event"] == "PollEnd":
            print(event_string[data["event"]].format(
                data["data"]["author"]["user_name"]))
            self.poll_switch = True

        elif data["event"] == "SkillAttribution":
            user = data["data"]["user_name"]
            skill = data["data"]["skill"]["skill_name"]
            sparks = data["data"]["skill"]["cost"]
            print(event_string["SkillAttribution"].format(
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
                    if user.lower() == "zoe_s17":
                        if target.lower() == "zoe_s17":
                            pass
                    else:
                        self.chat.whisper(user, f"{target} is away.")
                if target.lower() == "zoe_s17":
                    sys.__stdout__.write(f"{user} → {target} : {msg}\n")
                    sys.__stdout__.flush()

            elif "me" in data["data"]["message"]["meta"]:
                print(event_string["me"].format(
                    user=data["data"]["user_name"],
                    msg=msg))
            else:
                print(event_string[data["event"]].format(
                    user=data["data"]["user_name"],
                    msg=msg))
                if msg.startswith("We're now hosting @"):
                    print("-" * 80)
        else:
            print(f"[debug] {data}")

    def type_method(self, data):
        """ Handle the reply chat event types. """
        if self.config.CHATDEBUG:
            if data["method"] == "auth":
                pass

            elif data["method"] == "msg":
                if self.config.CHATDEBUG:
                    print("METHOD MSG: {}".format(str(data)))
            else:
                print("METHOD MSG: {}".format(str(data)))

    def type_system(self, data):
        """ Handle the reply chat event types. """
        if self.config.CHATDEBUG:
            print("SYSTEM MSG: {}".format(str(data["data"])))
