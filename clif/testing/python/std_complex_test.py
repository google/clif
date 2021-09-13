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

"""Tests for testing.python.std_complex."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import std_complex


@parameterized.parameters(std_complex.StdComplexFloat,
                          std_complex.StdComplexDouble)
class StdComplexTest(absltest.TestCase):

  def testZero(self, ctype):
    self.assertAlmostEqual(ctype.Zero(), complex(0))

  def testOne(self, ctype):
    self.assertAlmostEqual(ctype.One(), complex(1))

  def testI(self, ctype):
    self.assertAlmostEqual(ctype.i(), 1j)

  def testMultiply(self, ctype):
    self.assertAlmostEqual(ctype.Multiply(ctype.i(), ctype.i()), -ctype.One())


if __name__ == '__main__':
  absltest.main()
