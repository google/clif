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

import unittest

from extend_from_python.python import example


class ExampleTest(unittest.TestCase):

  def testAll(self):
    mc = example.MyClass()
    self.assertEqual(mc.f(), 1)
    self.assertIsNone(mc.g())
    self.assertEqual(mc.h(), 2)
    self.assertIsNone(mc.i(3))
    self.assertEqual(mc.j(5), 10)
    self.assertEqual(mc.k(7, 11), 25)


if __name__ == '__main__':
  unittest.main()
