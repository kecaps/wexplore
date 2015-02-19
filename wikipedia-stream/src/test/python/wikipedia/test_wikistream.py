#!/usr/bin/env python3
# -*- coding: utf-8; mode: python -*-

"""tests for wikistream"""

import json
import unittest

from wikipedia import wikistream


class TestWikiStream(unittest.TestCase):
    """Tests for wikistream."""

    def test_wikipedia_streamer(self):

        edit = None

        def set_edit(ev):
            nonlocal edit
            edit = ev

        streamer = wikistream.WikiStreamer(set_edit)
        streamer.process_until(lambda: edit is not None)
        self.assertIsNotNone(edit)

        print(json.dumps(edit, sort_keys=True, indent=2))


if __name__ == '__main__':
    unittest.main()
