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

"""Tests for clif.testing.python.operators."""

from absl.testing import absltest

from clif.testing.python import operators


class OperatorsTest(absltest.TestCase):

  def testAbc(self):
    abc = operators.Abc(ord('a'), ord('z'))
    self.assertEqual(bool(abc), False)
    self.assertEqual(int(abc), 1)
    self.assertAlmostEqual(float(abc), 1.1)
    self.assertLen(abc, 26)
    self.assertEqual(abc[0], ord('a'))
    self.assertEqual(abc[1], ord('b'))
    #    self.assertEqual(abc[-1], 'z')
    ABC = operators.Abc(ord('A'), ord('Z'))  # pylint: disable=invalid-name
    self.assertNotEqual(abc, ABC)
    self.assertEqual(len(abc), len(ABC))
    self.assertLess(ABC, abc, str(ABC[0] < abc[0]))
    abc += 2  # a->c
    self.assertLen(abc, 26)
    self.assertEqual(abc[0], ord('c'))
    self.assertIn(ord('c'), abc)
    self.assertLessEqual(ABC, abc, str(ABC[0] <= abc[0]))
    self.assertGreater(abc, ABC, str(abc[0] > ABC[0]))
    self.assertGreaterEqual(abc, ABC, str(abc[0] >= ABC[0]))

  def testNum(self):
    n = operators.Num()
    self.assertEqual(n%1, 1)
    self.assertEqual(2%n, 2)
    self.assertEqual(n+2, 2)
    with self.assertRaises(TypeError):
      _ = 2+n  # The lack of __radd__ makes this fail.
    self.assertEqual(3-n, 3)


if __name__ == '__main__':
  absltest.main()
