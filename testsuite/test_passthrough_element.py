# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4
#
# Copyright (C) 2015 Andrew Cook <ariscop@gmail.com>
# Copyright (C) 2015 Thibault Saunier <tsaunier@gnome.org>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

import sys
import overrides_hack
from common import TestCase
from gi.repository import GObject, Gst


Gst.init(None)

class Passthrough(Gst.Element):
    __gstmetadata__ = (
        "Passthrough element",
        "element.py",
        "Proxy buffers",
        "Andrew Cook <ariscop@gmail.com>"
    )

    _src_template = Gst.PadTemplate.new (
        'src',
        Gst.PadDirection.SRC,
        Gst.PadPresence.ALWAYS,
        Gst.caps_from_string('ANY')
    )
    _sink_template = Gst.PadTemplate.new (
        'sink',
        Gst.PadDirection.SINK,
        Gst.PadPresence.ALWAYS,
        Gst.caps_from_string('ANY')
    )

    _gsttemplates = (
        _src_template,
        _sink_template,
    )

    def __init__(self):
        Gst.Element.__init__(self)

        self.sinkpad = Gst.Pad.new_from_template(self._sink_template, 'sink')
        self.sinkpad.set_chain_function_full(self._sink_chain, None)
        self.sinkpad.set_event_function_full(self._sink_event, None)
        self.sinkpad.set_query_function_full(self._sink_query, None)
        self.add_pad(self.sinkpad)

        self.srcpad = Gst.Pad.new_from_template(self._src_template, 'src')
        self.srcpad.set_event_function_full(self._src_event, None)
        self.add_pad(self.srcpad)

    def __delete__(self):
        self.srcpad = None
        self.sinkpad = None

    def _sink_chain(self, pad, parent, buf):
        return self.srcpad.push(buf)

    def _sink_event(self, pad, parent, event):
        return self.srcpad.push_event(event)

    def _sink_query(self, pad, parent, query):
        if query.type == Gst.QueryType.CAPS:
            res = pad.proxy_query_caps(query)
        else:
            res = pad.query_default(parent, query)
        return res

    def _src_event(self, pad, parent, event):
        return self.sinkpad.push_event(event)

GObject.type_register(Passthrough)
Gst.Element.register(None, "testpassthrough", Gst.Rank.NONE, Passthrough)

class PassthroughElementTest(TestCase):
    def __init__(self, testCaseNames):
        TestCase.__init__(self, testCaseNames)
        self.loop = None
        self.pipeline = None
        self.bus = None

    def _errorOnBusCb(self, bus, message):
        pipeline.set_state(Gst.State.NULL)
        self.assert_(message.parse_error())

    def _eosCb(self, bus, message):
        self.loop.quit()
        self.pipeline.set_state(Gst.State.NULL)
        self.pipeline = None
        self.bus = None

    def testPassthrough(self):
        Gst.init(None)

        self.loop = GObject.MainLoop()
        Gst.segtrap_set_enabled(False)

        self.pipeline = Gst.parse_launch("videotestsrc num-buffers=10 ! testpassthrough ! autovideosink")

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message::error", self._errorOnBusCb)
        self.bus.connect("message::eos", self._eosCb)


        self.pipeline.set_state(Gst.State.PLAYING)

        self.loop.run()
