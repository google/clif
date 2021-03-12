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

"""Tests for testing.t1."""


from absl.testing import absltest
from absl.testing import parameterized
import six

from clif.testing.python import t1
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import t1_pybind11
except ImportError:
  t1_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('_c_api', '_pybind11'), (t1, t1_pybind11))
    if np[1] is not None
])
class T1Test(parameterized.TestCase):

  def testIntId(self, wrapper_lib):
    self.assertEqual(wrapper_lib.IntId(1), 1)
    self.assertEqual(wrapper_lib.IntId(x=1), 1)
    with self.assertRaises(TypeError):
      wrapper_lib.IntId(a=1)
    with self.assertRaises(TypeError):
      wrapper_lib.IntId()
    with self.assertRaises(TypeError):
      wrapper_lib.IntId(1, 2)

  def testSum3(self, wrapper_lib):
    self.assertEqual(wrapper_lib.Sum3(1, 2), 3)
    self.assertEqual(wrapper_lib.Sum3(1, b=2), 3)
    self.assertEqual(wrapper_lib.Sum3(a=1, b=2), 3)
    self.assertEqual(wrapper_lib.Sum3(b=2, a=1), 3)
    self.assertEqual(wrapper_lib.Sum3(b=2, c=3, a=1), 6)
    self.assertEqual(wrapper_lib.Sum3(1, 2, 3), 6)
    self.assertEqual(wrapper_lib.Sum3(1, 2, c=3), 6)
    with self.assertRaises(TypeError):
      wrapper_lib.Sum3()
    with self.assertRaises(TypeError):
      wrapper_lib.Sum3(1, b=2, x=1)
    with self.assertRaises(TypeError):
      wrapper_lib.Sum3(1, 2, 3, 4)
    self.assertEqual(wrapper_lib.Sum3(1, c=3), 4)

  def testString(self, wrapper_lib):
    self.assertEqual(wrapper_lib.StdString(), 'std')

  def testBytes(self, wrapper_lib):
    self.assertEqual(wrapper_lib.StdBytes(), b'std')

    # Pybind11 emulates python3 str/bytes behavior even when using python2.
    if six.PY2 and wrapper_lib is t1:
      self.assertEqual(wrapper_lib.UnicodeString(), u'\u0394'.encode('utf-8'))
    else:
      self.assertEqual(wrapper_lib.UnicodeString(), u'\u0394')

    self.assertEqual(wrapper_lib.UnicodeBytes(False), u'\u03B8'.encode('utf-8'))
    self.assertEqual(wrapper_lib.UnicodeBytes(True), b'\x80')

  def testFunctionDocstring(self, wrapper_lib):
    self.assertIn('function has a docstring.\n\n', wrapper_lib.Sum3.__doc__)
    self.assertIn('spans multiple lines', wrapper_lib.Sum3.__doc__)

  def testFunctionDocstringNoTrailingWhitespaces(self, wrapper_lib):
    if wrapper_lib is not t1:
      self.skipTest(
          'pybind11 automatically adds a trailing whitespace to function '
          'docstrings.')
    self.assertEqual(wrapper_lib.Sum3.__doc__, wrapper_lib.Sum3.__doc__.strip())


if __name__ == '__main__':
  absltest.main()
