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

"""Tests for clif.testing.python.t12."""

import unittest
from clif.testing.python import t12


class T12Test(unittest.TestCase):

  def testException(self):
    self.assertEqual(t12.f1(1), 2)
    with self.assertRaises(RuntimeError):
      t12.f2()


if __name__ == '__main__':
  unittest.main()
