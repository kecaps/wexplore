#!/usr/bin/env python3
# -*- coding: utf-8; mode: python -*-

import datetime
import logging
import os
import re
import socket

from irc import client as irc_client

from wikipedia import channels

DEFAULT_IRC = "irc.wikimedia.org"
DEFAULT_NICKNAME = "-".join(
    ("wikistream", re.sub(r"\W", "_", socket.gethostname()), str(os.getpid()))
)

RE_MESSAGE = re.compile(r"\x0314\[\[\x0307(.+?)\x0314\]\]\x034 (.*?)\x0310.*\x0302(.*?)\x03.+" \
        r"\x0303(.+?)\x03.+\x03 (.*) \x0310(.*)\u0003.*")

class WikiStreamer(object):

    def __init__(
        self,
        message_handler=print,
        irc_server=DEFAULT_IRC,
        nickname=DEFAULT_NICKNAME,
        channels=channels.WIKIPEDIAS.keys()
    ):
        self._num_messages = 0
        self._message_handler = message_handler
        self._client = irc_client.Reactor()
        self._client.add_global_handler("pubmsg", self.handle_event, -10)

        server = self._client.server()
        server.connect(irc_server, 6667, nickname)
        for channel in channels:
            server.join(channel)

    @property
    def num_messages(self):
        return self._num_messages

    def process_for(self, delta):
        start = datetime.datetime.now()
        end = start + delta
        logging.info("Running from %s to %s", start, end)
        self.process_until(lambda: datetime.datetime.now() >= end)

    def process_until(self, until=lambda: False):
        while not until():
            self._client.process_once(0.2)

    def parse_message(self, channel: str, msg: str):
        m = RE_MESSAGE.match(msg)
        if not m:
            return None
        groups = m.groups()
        try:
            delta = int(re.search(r"[+-]\d+", groups[4]).group())
        except:
            logging.warning("unable to parse delta string: %s", groups[4])
            delta = None

        # see if it looks like an anonymous edit
        user = groups[3];
        ipv4 = re.match(r"^\d+\.\d+\.\d+\.\d+$", user)
        ipv6 = re.match(r"^([0-9a-fA-F]*:){7}[0-9a-fA-F]*$", user)
        anonymous = ipv4 is not None or ipv6 is not None

        flag = groups[1];
        page = groups[0];
        wikipedia = channels.WIKIPEDIAS[channel]
        namespace = "article"
        if page and wikipedia:
            parts = page.split(":")
            if len(parts) > 1 and not parts[1].startswith(" "):
                namespace = wikipedia["namespaces"].get(parts[0], parts[0])

        return dict(
            wikipedia=wikipedia["short"],
            flag=flag,
            page=page,
            url=groups[2],
            delta=delta,
            comment=groups[5],
            user=user,
            anonymous=anonymous,
            namespace=namespace
        )

    def handle_event(self, connection, ev):
        if ev.arguments:
            msg = self.parse_message(ev.target, ev.arguments[0])
            if msg:
                self._num_messages += 1
                self._message_handler(msg)

    def close(self):
        if self._client.server().connected:
            self._client.server().disconnect()


if __name__ == "__main__":
    streamer = WikiStreamer()
    try:
        streamer.process_for(datetime.timedelta(seconds=5))
        print("Processed {} messages".format(streamer.num_messages))
    finally:
        streamer.close()