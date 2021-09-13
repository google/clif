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

"""Tests for clif.testing.python.t6."""

from absl.testing import absltest

from clif.testing.python import t6


class T6Test(absltest.TestCase):

  def testListInt(self):
    self.assertEqual(t6.Repeat([1, 2], 3), [1, 2, 1, 2, 1, 2])


if __name__ == '__main__':
  absltest.main()
