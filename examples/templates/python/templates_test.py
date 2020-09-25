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

"""Tests for clif.examples.templates.python.templates."""

import unittest
from templates.python import templates


class TemplatesTest(unittest.TestCase):

  def testTemplates(self):
    obj1 = templates.MyClassIntStr()
    obj1.a = 123
    obj1.b = 'abc'
    self.assertEqual(obj1.a, 123)
    self.assertEqual(obj1.b, 'abc')

    obj2 = templates.MyClassStrStr()
    obj2.a = 'hello'
    obj2.b = 'world'
    self.assertEqual(obj2.a, 'hello')
    self.assertEqual(obj2.b, 'world')

    self.assertEqual(templates.MyAddInt(120, 3), 123)
    self.assertEqual(templates.MyAddFloat(12, 0.3), 12.3)


if __name__ == '__main__':
  unittest.main()

