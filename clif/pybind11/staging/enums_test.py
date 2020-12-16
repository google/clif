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

"""Tests for clif.pybind11.staging.enums.

This file is a copy of clif/testing/python/t3_test.py.
"""

import unittest
from clif.pybind11.staging import enums


class EnumsTest(unittest.TestCase):

  def testEnum(self):
    self.assertEqual(enums._Old.TOP1, 1)
    self.assertEqual(enums._Old.TOPn, -1)
    self.assertNotEqual(enums._New.TOP, 1)
    self.assertEqual(enums._New.TOP.name, 'TOP')
    self.assertTrue(enums._New.BOTTOM)
    self.assertEqual(enums._New.BOTTOM, enums._New(1))
    self.assertEqual(enums._New.TOP, enums._New(1000))
    self.assertEqual(enums.K.OldE.ONE, 1)
    self.assertEqual(enums.K.NewE.ONE, enums.K.NewE(11))
    self.assertRaises(TypeError, enums.K().M, (5))
    # This is necessary for proper pickling.
    self.assertEqual(enums._New.__module__, enums.__name__)


if __name__ == '__main__':
  unittest.main()
