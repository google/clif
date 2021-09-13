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

from clif.testing.python import t1


class T1Test(absltest.TestCase):

  def testIntId(self):
    self.assertEqual(t1.IntId(1), 1)
    self.assertEqual(t1.IntId(x=1), 1)
    with self.assertRaises(TypeError):
      t1.IntId(a=1)
    with self.assertRaises(TypeError):
      t1.IntId()
    with self.assertRaises(TypeError):
      t1.IntId(1, 2)

  def testSum3(self):
    self.assertEqual(t1.Sum3(1, 2), 3)
    self.assertEqual(t1.Sum3(1, b=2), 3)
    self.assertEqual(t1.Sum3(a=1, b=2), 3)
    self.assertEqual(t1.Sum3(b=2, a=1), 3)
    self.assertEqual(t1.Sum3(b=2, c=3, a=1), 6)
    self.assertEqual(t1.Sum3(1, 2, 3), 6)
    self.assertEqual(t1.Sum3(1, 2, c=3), 6)
    with self.assertRaises(TypeError):
      t1.Sum3()
    with self.assertRaises(TypeError):
      t1.Sum3(1, b=2, x=1)
    with self.assertRaises(TypeError):
      t1.Sum3(1, 2, 3, 4)
    self.assertEqual(t1.Sum3(1, c=3), 4)

  def testString(self):
    self.assertEqual(t1.StdString(), 'std')

  def testBytes(self):
    self.assertEqual(t1.StdBytes(), b'std')

    self.assertEqual(t1.UnicodeString(), u'\u0394')

    self.assertEqual(t1.UnicodeBytes(False), u'\u03B8'.encode('utf-8'))
    self.assertEqual(t1.UnicodeBytes(True), b'\x80')

  def testFunctionDocstring(self):
    self.assertIn('function has a docstring.\n\n', t1.Sum3.__doc__)
    self.assertIn('spans multiple lines', t1.Sum3.__doc__)

  def testFunctionDocstringNoTrailingWhitespaces(self):
    if 'pybind11' in t1.__doc__:
      self.skipTest(
          'pybind11 automatically adds a trailing whitespace to function '
          'docstrings.')
    self.assertEqual(t1.Sum3.__doc__, t1.Sum3.__doc__.strip())


if __name__ == '__main__':
  absltest.main()
