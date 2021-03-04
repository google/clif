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
"""Tests for clif.pybind11.staging.concrete."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.pybind11.staging import concrete_base
from clif.pybind11.staging import concrete_derived

CONCRETE_BASE_EMPTY_GET_RESULT = 90146438
CONCRETE_DERIVED_EMPTY_GET_RESULT = 31607978


class ConcreteTest(parameterized.TestCase):

  def testBaseAndDerived(self):
    cbe = concrete_base.ConcreteBaseEmpty()
    self.assertEqual(cbe.Get(), CONCRETE_BASE_EMPTY_GET_RESULT)
    cde = concrete_derived.ConcreteDerivedEmpty()
    self.assertEqual(cde.Get(), CONCRETE_DERIVED_EMPTY_GET_RESULT)
    self.assertEqual(
        cde.BaseGet(cbe),
        CONCRETE_BASE_EMPTY_GET_RESULT + CONCRETE_DERIVED_EMPTY_GET_RESULT)
    self.assertEqual(
        cde.BaseGet(cde),
        CONCRETE_BASE_EMPTY_GET_RESULT + CONCRETE_DERIVED_EMPTY_GET_RESULT)


if __name__ == '__main__':
  absltest.main()
