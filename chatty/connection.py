#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Handles the connection to Mixer Chat servers."""

import requests
from .evented import Evented
from .socket import Socket
from .errors import NotAuthenticatedError


class Connection(Evented):
    """Connection Class"""

    def __init__(self, config):
        super(Connection, self).__init__()
        self.config = config
        self.chat_details = None
        self.userid = None
        self.username = None

    def _buildurl(self, path):
        """Create an address to Mixer with the given path."""
        return self.config.Mixer_URI + path

    def _get_chat_details(self):
        """Get chat connection details from Mixer."""
        # Create the header for the request
        header = {'Media-Type': 'application/json',
                  'Authorization': 'Bearer ' + self.config.ACCESS_TOKEN}
        # Get the request and return the responce
        url = self._buildurl(self.config.CHATSCID_URI.format(
            cid=self.config.CHANNELID))
        self.chat_details = requests.get(url=url, headers=header).json()
        url = self._buildurl(self.config.USERSCURRENT_URI)
        self.userid = requests.get(url=url, headers=header).json()
        self.username = self.userid["username"]
        self.userid = self.userid["id"]

    def _connect_to_chat(self):
        """Connect to the chat websocket."""
        if self.chat_details is None:
            raise NotAuthenticatedError("You must first log in to Mixer!")

        self.websocket = Socket(self.chat_details["endpoints"])
        self.websocket.on("opened", self._send_auth_packet)
        self.websocket.on("message", lambda msg: self.emit("message", msg))

    def _send_auth_packet(self):
        """Send an authentication packet to the chat server."""
        self.websocket.send(
            "method",
            self.config.CHANNELID, self.userid, self.chat_details["authkey"],
            method="auth")

    def authenticate(self):
        """Get Mixer connection info and connects to the chat server."""
        self._get_chat_details()
        self._connect_to_chat()

    def message(self, msg):
        """Send a chat message."""
        self.websocket.send("method", msg, method="msg")

    def whisper(self, target, msg):
        """Send a whisper message."""
        self.websocket.send("method", target, msg, method="whisper")

    def purge(self, target):
        """
        Purge a user by name.

        :param: target: User to purge
        :type target: String
        """
        self.websocket.send("method", target, method="purge")

    def delete_msg(self, mid):
        """
        Delete a message by ID.

        :param: mid: Message ID
        :type mid: UUID
        """
        self.websocket.send("method", mid, method="deleteMessage")

    def clear_chat(self):
        """
        Clears chat we're in
        """
        self.websocket.send("method", mid, method="clearMessages")