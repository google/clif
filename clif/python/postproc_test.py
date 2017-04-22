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

"""Tests for clif.python.postproc."""

import unittest
from clif.python import postproc


class PostprocTest(unittest.TestCase):

  def testValueErrorOnFalse(self):
    self.assertEqual(postproc.ValueErrorOnFalse(True, 1), 1)
    self.assertEqual(postproc.ValueErrorOnFalse(True, 1, 2), (1, 2))
    with self.assertRaises(ValueError):
      postproc.ValueErrorOnFalse(False)
    with self.assertRaises(ValueError):
      postproc.ValueErrorOnFalse(False, 1)
    with self.assertRaises(TypeError):
      postproc.ValueErrorOnFalse(0)
    with self.assertRaises(TypeError):
      postproc.ValueErrorOnFalse(0, 1)

if __name__ == '__main__':
  unittest.main()
