# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for clif.python.proto."""

import logging
import unittest
from clif.python import proto

proto_util = proto.proto_util
PKG = ''
TEST_SRCDIR = '/tmp'


class ProtoTest(unittest.TestCase):

  def testCreateTypeInfo(self):
    test_proto = PKG + 'testdata/test.proto'
    logging.info(test_proto)
    d = proto_util.ProtoFileInfo(test_proto, TEST_SRCDIR)
    self.assertTrue(d, d.ErrorMsg())
    msgs = proto.CreatePyTypeInfo(d, 'a/b/c')
    m = {}
    ns = '::clif::python::testdata::'
    for t in msgs:
      self.assertTrue(t.cname.startswith(ns))
      m[t.cname] = t.pyname

    self.assertEqual(m[ns+'TopLevelMessage'], 'TopLevelMessage')
    self.assertEqual(m[ns+'TopLevelEnum'], 'TopLevelEnum')

    self.assertEqual(m[ns+'TopLevelMessage::NestedEnum'],
                     'TopLevelMessage.NestedEnum')
    self.assertEqual(m[ns+'TopLevelMessage::NestedMessage'],
                     'TopLevelMessage.NestedMessage')
    self.assertEqual(m[ns+'TopLevelMessage::GroupMessage'],
                     'TopLevelMessage.GroupMessage')

    self.assertEqual(m[ns+'TopLevelMessage::NestedMessage::DoublyNestedEnum'],
                     'TopLevelMessage.NestedMessage.DoublyNestedEnum')

  def testNoPkg(self):
    d = proto_util.ProtoFileInfo(PKG+'testdata/no_pkg.proto.data', TEST_SRCDIR)
    with self.assertRaises(ValueError):
      _ = proto.CreatePyTypeInfo(d, 'a/b/c')


if __name__ == '__main__':
  unittest.main()
