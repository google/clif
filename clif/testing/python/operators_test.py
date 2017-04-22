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

import unittest
from clif.testing.python import operators


class OperatorsTest(unittest.TestCase):

  def testAbc(self):
    abc = operators.Abc(ord('a'), ord('z'))
    self.assertEqual(len(abc), 26)
    self.assertEqual(abc[0], 'a')
    self.assertEqual(abc[1], 'b')
    self.assertEqual(abc[-1], 'z')
    ABC = operators.Abc(ord('A'), ord('Z'))  # pylint: disable=invalid-name
    self.assertNotEqual(abc, ABC)
    self.assertEqual(len(abc), len(ABC))
    self.assertLess(ABC, abc, str(ABC[0] < abc[0]))


if __name__ == '__main__':
  unittest.main()
