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

"""Tests for postconv."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import textwrap
import unittest
from google.protobuf import text_format
from clif.protos import ast_pb2
from clif.python import postconv


class PostconvTest(unittest.TestCase):
  # pylint: disable=g-short-docstring-punctuation

  def testEmptyTransform(self):
    output = list(postconv.GenPostConvTable({}))
    self.assertFalse(output)

  def testTransform(self):
    postconversion = {'str': 'BytesToUnicode', 'ztype': 'AnotherConversion'}
    output = '\n'.join(postconv.GenPostConvTable(postconversion))
    self.assertEqual(postconversion, {'str': '_1', 'ztype': '_2'})
    self.assertMultiLineEqual(output, textwrap.dedent("""
      #define _0 py::postconv::PASS
      #define _1 BytesToUnicode
      #define _2 AnotherConversion"""))

  def testPatternInt(self):
    """int -> {}"""
    index = {'str': 1, 'ztype': 2}
    ast_type = ast_pb2.Type()
    text_format.Parse("""
        lang_type: "int"
      """, ast_type)
    self.assertEqual(postconv.Initializer(ast_type, index), '{}')

  def testPatternStr(self):
    """str -> _1"""
    index = {'str': '_1', 'ztype': '_2'}
    ast_type = ast_pb2.Type()
    text_format.Parse("""
        lang_type: "str"
      """, ast_type)
    self.assertEqual(postconv.Initializer(ast_type, index), '_1')

  def testPatternListInt(self):
    """list<int> -> {}"""
    index = {'str': '_1', 'ztype': '_2'}
    ast_type = ast_pb2.Type()
    text_format.Parse("""
        lang_type: "list<int>"
        params {
          lang_type: "int"
        }
      """, ast_type)
    self.assertEqual(postconv.Initializer(ast_type, index), '{}')

  def testPatternListStr(self):
    """list<str> -> {_1}"""
    index = {'str': '_1', 'ztype': '_2'}
    ast_type = ast_pb2.Type()
    text_format.Parse("""
        lang_type: "list<str>"
        params {
          lang_type: "str"
        }
      """, ast_type)
    self.assertEqual(postconv.Initializer(ast_type, index), '{_1}')

  def testPatternNested(self):
    """dict<int, tuple<str, ztype>> -> {_0,{_1,_2}}"""
    index = {'str': '_1', 'ztype': '_2'}
    ast_type = ast_pb2.Type()
    text_format.Parse("""
        lang_type: "dict<int, tuple<str, ztype>>"
        params {
          lang_type: "int"
        }
        params {
          lang_type: "tuple<str, ztype>"
          params {
            lang_type: "str"
          }
          params {
            lang_type: "ztype"
          }
        }
      """, ast_type)
    self.assertEqual(postconv.Initializer(ast_type, index), '{_0,{_1,_2}}')

  def testPatternCustom(self):
    """StatusOr<str> -> {_1}"""
    index = {'str': '_1', 'ztype': '_2'}
    ast_type = ast_pb2.Type()
    text_format.Parse("""
        lang_type: "StatusOr<str>"
        params {
          lang_type: "str"
        }
      """, ast_type)
    self.assertEqual(postconv.Initializer(ast_type, index), '{_1}')


if __name__ == '__main__':
  unittest.main()
