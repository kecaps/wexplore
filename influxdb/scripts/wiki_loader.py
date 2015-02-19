#!/usr/bin/env python3
# -*- coding: utf-8; mode: python -*-

"""Load wiki events into a influxdb"""

import argparse
import datetime
import os
import re
import sys

import influxdb
import influxdb.client


from wikipedia import channels
from wikipedia import wikistream


# --------------------------------------------------------------------------------------------------


def influx_streamer(influx: influxdb.InfluxDBClient, *args, **kwargs):

    streamer = None

    def write_point(msg):
        influx.write_points(
            [{"name": "edits", "points": [list(msg.values())], "columns": list(msg.keys())}],
            time_precision="ms"
        )
        if streamer.num_messages % 100 == 99:
            sys.stderr.write("Written {} messages...\n".format(streamer.num_messages+1))

    streamer = wikistream.WikiStreamer(write_point, *args, **kwargs)
    return streamer



# --------------------------------------------------------------------------------------------------


# Regular expression used for parsing timedelta strings.
# Each line is a combination of numeric multiplier and string describing the unit. This will match
# unit descriptions that are abbreviated or pluralized.
_TIME_DELTA_RE = re.compile(
    r"""
    ^
    (?:(?P<weeks>\d+)\s*w(?:eeks?)?\s*)?
    (?:(?P<days>\d+)\s*d(?:ays?)?\s*)?
    (?:(?P<hours>\d+)\s*h(?:ours?|r)?\s*)?
    (?:(?P<minutes>\d+)\s*m(?:in(?:ute)?s?)?\s*)?
    (?:(?P<seconds>\d+)\s*s(?:ec(?:ond)?s?)?\s*)?
    (?:(?P<milliseconds>\d+)\s*(?:ms|milliseconds?)?\s*)?
    (?:(?P<microseconds>\d+)\s*(?:us|microseconds?)?\s*)?
    $
    """,
    flags=re.IGNORECASE | re.VERBOSE
)


def parse_timedelta(text):
    """Parse a timedelta from a string.

    The string is composed of a sequence of tuples of multiplier and time unit in decreasing
    time unit order. The following time units are supported:
        week (w)
        day (d)
        hour (h)
        minute (m or min)
        second (s or sec)
        milliseconds (ms)
        microseconds (us)

    As an example,
        parse_timedelta("1w2h3s4us") == timedelta(days=7, hours=2, seconds=3, microseconds=4)

    Args:
        text: String to be parsed as a timedelta.
    Returns:
        datetime.timedelta object constructed from text.
    """
    parts = _TIME_DELTA_RE.match(text)
    if not parts:
        raise ValueError("bad format for timedelta: {}".format(text))
    parts = dict(
        (key, int(value))
        for key, value in parts.groupdict().items()
        if value is not None
    )
    td = datetime.timedelta(**parts)
    return td


def connect_influx(database=None, **kwargs):
    print("Connecting to influx database '{}' with parameters: {}".format(database, kwargs))
    client = influxdb.InfluxDBClient(**kwargs)
    if database:
        try:
            client.create_database(database)
        except influxdb.client.InfluxDBClientError as client_err:
            if client_err.code == 409:
                client.switch_database(database)
            else:
                raise client_err
    return client

# --------------------------------------------------------------------------------------------------


def influx_args(loc):
    m = re.match(r"^(?:(?:(\w+)/(\w+)@)?(\w+)(?::(\d+))?)?(?:/(.+))?$", loc)
    if not m:
        raise ValueError("Bad format for influxdb location: {}".format(loc))
    args = {}
    groups = m.groups()
    for ndx, keyword in enumerate(("username", "password", "host")):
        if groups[ndx]:
            args[keyword] = groups[ndx]
    if groups[-2]:
        args["port"] = int(groups[-2])
    if groups[-1]:
        args["database"] = groups[-1]
    return args


# --------------------------------------------------------------------------------------------------


def main(argv):

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--influx",
        type=influx_args,
        default={},
        help="connection string for influxdb. The format is user/password@host:port/database."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--num-events", type=int, help="Load a certain number of events.")
    group.add_argument("--until", type=parse_timedelta, help="Load events for a period of time.")
    parser.add_argument(
        "--channels",
        choices=list(channels.WIKIPEDIAS.keys()),
        nargs='*',
        default=channels.WIKIPEDIAS.keys(),
        help="Which wikipedia channels to connect to."
    )
    args = parser.parse_args(argv)

    influx = connect_influx(**args.influx)
    streamer = influx_streamer(influx, channels=args.channels)
    try:
        start = datetime.datetime.now()
        until = lambda: False
        if args.num_events:
            print("Processing {} events.".format(args.num_events))
            until = lambda: streamer.num_messages >= args.num_events
        elif args.until:
            print("Processing until {} elapses.".format(args.until))
            end = start + args.until
            until = lambda: datetime.datetime.now() >= end
        else:
            raise ValueError("Must specify num_events or until")
        streamer.process_until(until=until)
        print("Processed {} events from {} to {}".format(streamer.num_messages, start, end))
    finally:
        streamer.close()


if __name__ == "__main__":
    main(sys.argv[1:])