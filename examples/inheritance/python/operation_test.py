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

"""Tests for clif.examples.inheritence.python.operation."""

import unittest
from inheritance.python import operation


class Add(operation.Operation):

  def __init__(self, a, b):
    operation.Operation.__init__(self)
    self.a = a
    self.b = b

  def Run(self):
    return self.a + self.b


class OperationTest(unittest.TestCase):

  def testAddOperation(self):
    add = Add(120, 3)
    r = operation.Perform(add)
    self.assertEqual(r, 123)


if __name__ == '__main__':
  unittest.main()
