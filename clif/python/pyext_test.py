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

"""Tests for pyext."""

import os
import textwrap
import unittest
from clif.python import pyext
from clif.python import pytd2proto
from clif.python import pytd_parser
from clif.python import clif_types as types

# The unit tests are run from a build directory outside of the source directory.
# Hence, it is OK to create a file in the build directory only for testing.
TMP_FILE = 'clif_python_pyext_test'


def _ParseFile(pytd, type_headers):
  with open(TMP_FILE, 'w') as pytd_file:
    pytd_file.write(pytd)
  p = pytd2proto.Postprocessor(
      config_headers=type_headers,
      include_paths=[os.environ['CLIF_DIR']])
  with open(TMP_FILE, 'r') as pytd_file:
    pb = p.Translate(pytd_file)
  return pb


class TypesNsTest(unittest.TestCase):

  def setUp(self):
    super().setUp()
    pytd_parser.reset_indentation()

  def assertNsEqual(self, proto, ns):
    pytd = textwrap.dedent(proto)
    ast = _ParseFile(pytd, type_headers=['clif/python/types.h'])
    m = pyext.Module('my.path.py.ext')
    for d in ast.decls:
      list(m.WrapDecl(d))
    if m.types:
      different_ns = set(types.Namespace(t) for t in m.types)
      self.assertEqual(set(ns), different_ns)
    else:
      self.assertFalse(ns)

  def testTypesNs0(self):
    self.assertNsEqual("""\
      from "my/path/ext.h":
        class A:
          class B:
            x: int
    """, [''])

  def testTypesNs1(self):
    self.assertNsEqual("""\
      from "my/path/ext.h":
        namespace `a`:
          class A:
            class B:
              x: int
    """, ['a'])

  def testTypesNs2(self):
    self.assertNsEqual("""\
      from "my/path/ext.h":
        namespace `a`:
          class A:
            \"\"\"This is a docstring.\"\"\"
            class B:
              x: int
        namespace `b::c`:
          class D:
            y: int
    """, ['a', 'b::c'])


if __name__ == '__main__':
  unittest.main()
