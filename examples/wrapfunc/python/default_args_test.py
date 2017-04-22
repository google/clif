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

"""Tests for clif.examples.wrapfunc.python.default_args.
"""

import absolute_import
import division
import print_function

import unittest
import default_args


class DefaultArgTest(unittest.TestCase):

  def testDefaultArgTest(self):
    self.assertTrue(default_args.Inc(5), 6)
    self.assertTrue(default_args.Inc(5, 2), 7)

    self.assertTrue(default_args.Scale(5), 10)
    self.assertTrue(default_args.Scale(5, offset=10), 30)
    with self.assertRaises(ValueError):
      default_args.ScaleWithRatios(5, offset=10)


if __name__ == '__main__':
  unittest.main()
