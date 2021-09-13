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

"""Tests for clif.testing.python.diamond_inheritance."""

from absl.testing import absltest

from clif.testing.python import diamond_inheritance


class DiamondInheritanceTest(absltest.TestCase):

  def testDiamondInheritance(self):
    d = diamond_inheritance.Derived3_int()
    d.SetBaseValue(100)
    self.assertEqual(d.GetBaseValue(), 100)


if __name__ == '__main__':
  absltest.main()
