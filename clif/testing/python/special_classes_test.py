# Copyright 2020 Google LLC
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

"""Tests for clif.testing.python.special_classes."""

from absl.testing import absltest

from clif.testing.python import special_classes


def expected_exception():
  return TypeError if 'pybind11' in special_classes.__doc__ else ValueError


class SpecialClassesTest(absltest.TestCase):

  def testAbstract(self):
    self.assertTrue(special_classes.Abstract.Future)
    self.assertRaises(expected_exception(), special_classes.Abstract)
    self.assertEqual(special_classes.Abstract.KIND, 'pure virtual',
                     str(type(special_classes.Abstract.KIND)))

  def testInconstructibleStaticMethod(self):
    self.assertEqual(special_classes.InconstructibleF(), 0)

  def testNoDefaultConstructor(self):
    with self.assertRaises(expected_exception()):
      # true error, no def ctor
      _ = special_classes.NoDefaultConstructor().a
    with self.assertRaises(expected_exception()):
      # true error, non-def ctor not wrapped
      _ = special_classes.NoDefaultConstructor(1).a

  def testNoCopy(self):
    no_copy = special_classes.NoCopy(1)
    self.assertEqual(no_copy.a, 1)

  def testNoMove(self):
    no_move = special_classes.NoMove(1)
    self.assertEqual(no_move.a, 1)


if __name__ == '__main__':
  absltest.main()
