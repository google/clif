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

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.derived_in_other_header.python import concrete_base
from clif.testing.derived_in_other_header.python import concrete_derived
from clif.testing.derived_in_other_header.python import shared_unique_interop
from clif.testing.derived_in_other_header.python import virtual_derived

# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.derived_in_other_header.python import concrete_base_pybind11
  from clif.testing.derived_in_other_header.python import concrete_derived_pybind11
  from clif.testing.derived_in_other_header.python import shared_unique_interop_pybind11
  from clif.testing.derived_in_other_header.python import virtual_derived_pybind11
except ImportError:
  concrete_base_pybind11 = None
  concrete_derived_pybind11 = None
  shared_unique_interop_pybind11 = None
  virtual_derived_pybind11 = None
# pylint: enable=g-import-not-at-top

CONCRETE_BASE_EMPTY_GET_RESULT = 90146438
CONCRETE_DERIVED_EMPTY_GET_RESULT = 31607978
VIRTUAL_DERIVED_EMPTY_GET_RESULT = 29852452


class ConcreteTest(parameterized.TestCase):

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.concrete_base = concrete_base
    cls.concrete_derived = concrete_derived
    cls.shared_unique_interop = shared_unique_interop

  def testBaseAndDerived(self):
    cbe = self.concrete_base.ConcreteBaseEmpty()
    self.assertEqual(cbe.Get(), CONCRETE_BASE_EMPTY_GET_RESULT)
    cde = self.concrete_derived.ConcreteDerivedEmpty()
    self.assertEqual(cde.Get(), CONCRETE_DERIVED_EMPTY_GET_RESULT)
    self.assertEqual(
        cde.BaseGet(cbe),
        CONCRETE_BASE_EMPTY_GET_RESULT + CONCRETE_DERIVED_EMPTY_GET_RESULT)
    self.assertEqual(
        cde.BaseGet(cde),
        CONCRETE_BASE_EMPTY_GET_RESULT + CONCRETE_DERIVED_EMPTY_GET_RESULT)

  @parameterized.named_parameters(
      ('DefaultDeleter', False),
      ('CustomDeleter', True))
  def testUnableToDisownOriginalShared(self, use_custom_deleter):
    cbe = self.shared_unique_interop.make_shared_concrete_derived_empty_up_cast(
        use_custom_deleter)
    with self.assertRaises(ValueError):
      self.shared_unique_interop.pass_unique_concrete_base_empty(cbe)

  def testPassUniqueConcreteBaseEmpty(self):
    # b/175568410
    cbe = (
        self.shared_unique_interop.make_unique_concrete_derived_empty_up_cast())
    self.assertEqual(cbe.Get(), CONCRETE_BASE_EMPTY_GET_RESULT)
    i = self.shared_unique_interop.pass_unique_concrete_base_empty(cbe)
    self.assertEqual(i, CONCRETE_BASE_EMPTY_GET_RESULT)
    with self.assertRaises(ValueError):  # Disowned.
      cbe.Get()

  def testOriginalUniqueNotDisownedByShared(self):
    # b/175568410
    cbe = (
        self.shared_unique_interop.make_unique_concrete_derived_empty_up_cast())
    i = self.shared_unique_interop.pass_shared_concrete_base_empty(cbe)
    self.assertEqual(i, CONCRETE_BASE_EMPTY_GET_RESULT)
    self.assertEqual(cbe.Get(), CONCRETE_BASE_EMPTY_GET_RESULT)
    i = self.shared_unique_interop.pass_unique_concrete_base_empty(cbe)
    self.assertEqual(i, CONCRETE_BASE_EMPTY_GET_RESULT)
    with self.assertRaises(ValueError):  # Disowned.
      cbe.Get()

  @parameterized.named_parameters(
      ('DefaultDeleter', False),
      ('CustomDeleter', True))
  def testPassSharedConcreteBaseEmpty(self, use_custom_deleter):
    cbe = self.shared_unique_interop.make_shared_concrete_derived_empty_up_cast(
        use_custom_deleter)
    self.assertEqual(cbe.Get(), CONCRETE_BASE_EMPTY_GET_RESULT)
    i = self.shared_unique_interop.pass_shared_concrete_base_empty(cbe)
    self.assertEqual(i, CONCRETE_BASE_EMPTY_GET_RESULT)
    self.assertEqual(cbe.Get(), CONCRETE_BASE_EMPTY_GET_RESULT)


@absltest.skipIf(not concrete_base_pybind11, 'Failed to import pybind11 module')
class ConcretePybind11Test(ConcreteTest):

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.concrete_base = concrete_base_pybind11
    cls.concrete_derived = concrete_derived_pybind11
    cls.shared_unique_interop = shared_unique_interop_pybind11


class VirtualTest(parameterized.TestCase):

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.shared_unique_interop = shared_unique_interop
    cls.virtual_derived = virtual_derived

  def testBaseAndDerived(self):
    vde = self.virtual_derived.VirtualDerivedEmpty()
    self.assertEqual(vde.Get(), VIRTUAL_DERIVED_EMPTY_GET_RESULT)
    self.assertEqual(vde.BaseGet(vde), 2 * VIRTUAL_DERIVED_EMPTY_GET_RESULT)

  @parameterized.named_parameters(
      ('DefaultDeleter', False),
      ('CustomDeleter', True))
  def testUnableToDisownOriginalShared(self, use_custom_deleter):
    vbe = self.shared_unique_interop.make_shared_virtual_derived_empty_up_cast(
        use_custom_deleter)
    with self.assertRaises(ValueError):
      self.shared_unique_interop.pass_unique_virtual_base_empty(vbe)

  def testPassUniqueVirtualBaseEmpty(self):
    vbe = self.shared_unique_interop.make_unique_virtual_derived_empty_up_cast()
    self.assertEqual(vbe.Get(), VIRTUAL_DERIVED_EMPTY_GET_RESULT)
    i = self.shared_unique_interop.pass_unique_virtual_base_empty(vbe)
    self.assertEqual(i, VIRTUAL_DERIVED_EMPTY_GET_RESULT)
    with self.assertRaises(ValueError):  # Disowned.
      vbe.Get()

  def testOriginalUniqueNotDisownedByShared(self):
    vbe = self.shared_unique_interop.make_unique_virtual_derived_empty_up_cast()
    i = self.shared_unique_interop.pass_shared_virtual_base_empty(vbe)
    self.assertEqual(i, VIRTUAL_DERIVED_EMPTY_GET_RESULT)
    self.assertEqual(vbe.Get(), VIRTUAL_DERIVED_EMPTY_GET_RESULT)
    i = self.shared_unique_interop.pass_unique_virtual_base_empty(vbe)
    self.assertEqual(i, VIRTUAL_DERIVED_EMPTY_GET_RESULT)
    with self.assertRaises(ValueError):  # Disowned.
      vbe.Get()

  @parameterized.named_parameters(
      ('DefaultDeleter', False),
      ('CustomDeleter', True))
  def testPassSharedVirtualBaseEmpty(self, use_custom_deleter):
    vbe = self.shared_unique_interop.make_shared_virtual_derived_empty_up_cast(
        use_custom_deleter)
    self.assertEqual(vbe.Get(), VIRTUAL_DERIVED_EMPTY_GET_RESULT)
    i = self.shared_unique_interop.pass_shared_virtual_base_empty(vbe)
    self.assertEqual(i, VIRTUAL_DERIVED_EMPTY_GET_RESULT)
    self.assertEqual(vbe.Get(), VIRTUAL_DERIVED_EMPTY_GET_RESULT)


@absltest.skipIf(not virtual_derived_pybind11,
                 'Failed to import pybind11 module')
class VirtualPybind11Test(VirtualTest):

  @classmethod
  def setUpClass(cls):
    super().setUpClass()
    cls.shared_unique_interop = shared_unique_interop_pybind11
    cls.virtual_derived = virtual_derived_pybind11


if __name__ == '__main__':
  absltest.main()
