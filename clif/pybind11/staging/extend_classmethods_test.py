# Copyright 2021 Google LLC
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

"""Tests for clif.pybind11.staging.extend_classmethods.

This file is a copy of
clif/testing/python/extend_classmethods_test.py.
"""

import unittest
from clif.pybind11.staging import extend_classmethods


class ExtendClassmethodsTest(unittest.TestCase):

  def test_create_from_value(self):
    expected_value = 543
    abc = extend_classmethods.Abc.from_value(expected_value)
    self.assertEqual(abc.get_value(), expected_value)

  def test_set_class_variable(self):
    expected_value = 5432
    extend_classmethods.Abc.set_static_value(expected_value)
    self.assertEqual(extend_classmethods.Abc.get_static_value(), expected_value)


if __name__ == '__main__':
  unittest.main()
