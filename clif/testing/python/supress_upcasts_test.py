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

"""Tests for clif.testing.python.supress_upcasts."""

import unittest
from clif.testing.python import supress_upcasts


class SupressUpcastsTest(unittest.TestCase):

  def testClassWithoutUpcasts(self):
    obj = supress_upcasts.DerivedSupressUpcasts()
    self.assertEqual(obj.value(), 20)


if __name__ == '__main__':
  unittest.main()
