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

"""Tests for clif.testing.python.t3."""

import unittest
from clif.testing.python import t3


class T3Test(unittest.TestCase):

  def testEnum(self):
    self.assertEqual(t3._Old.TOP1, 1)
    self.assertEqual(t3._Old.TOPn, -1)
    self.assertNotEqual(t3._New.TOP, 1)
    self.assertEqual(t3._New.TOP.name, 'TOP')
    self.assertTrue(t3._New.BOTTOM)
    self.assertEqual(t3._New.BOTTOM, t3._New(1))
    self.assertEqual(t3._New.TOP, t3._New(1000))
    self.assertEqual(t3.K.OldE.ONE, 1)
    self.assertEqual(t3.K.NewE.ONE, t3.K.NewE(11))
    self.assertRaises(TypeError, t3.K().M, (5))
    # This is necessary for proper pickling.
    self.assertEqual(t3._New.__module__, t3.__name__)

if __name__ == '__main__':
  unittest.main()
