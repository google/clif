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

"""Tests for clif.pybind11.staging.static_methods.

This file is a copy of clif/testing/python/static_methods_test.
"""

import unittest

from clif.pybind11.staging import static_methods


class StaticMethodsTest(unittest.TestCase):

  def testStaticMethods(self):
    self.assertEqual(static_methods.MethodWithNoArgs().a, 123)
    self.assertEqual(static_methods.MethodWithOneArg(321).a, 321)


if __name__ == '__main__':
  unittest.main()
