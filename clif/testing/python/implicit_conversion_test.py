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

"""Tests for clif.testing.python.implicit_conversion."""

import unittest
from clif.testing.python import implicit_conversion


class ImplicitConversionTest(unittest.TestCase):

  def testImplicitConversion(self):
    b = implicit_conversion.B(123)
    self.assertEqual(implicit_conversion.Func(b), 123)


if __name__ == '__main__':
  unittest.main()
