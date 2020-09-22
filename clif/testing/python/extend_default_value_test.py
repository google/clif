# Lint-as: python3

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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest

from clif.testing.python import extend_default_value


class ExtendDefaultValueTest(unittest.TestCase):

  def test_only_default_values(self):
    v1 = 10
    v2 = 100
    expected_value = v1 + v2
    abc = extend_default_value.Abc(v1)
    self.assertEqual(abc.get_value(), v1)
    abc.sum_and_set_values()
    self.assertEqual(abc.get_value(), expected_value)

  def test_one_default_value(self):
    v1 = 123
    v2 = 100
    expected_value = v1 + v2
    abc = extend_default_value.Abc(v1)
    self.assertEqual(abc.get_value(), v1)
    abc.sum_and_set_values(v1=v1)
    self.assertEqual(abc.get_value(), expected_value)

  def test_not_using_default_value(self):
    v1 = 123
    v2 = 456
    expected_value = v1 + v2
    abc = extend_default_value.Abc(v1)
    self.assertEqual(abc.get_value(), v1)
    abc.sum_and_set_values(v1=v1, v2=v2)
    self.assertEqual(abc.get_value(), expected_value)


if __name__ == '__main__':
  unittest.main()
