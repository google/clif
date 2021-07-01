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

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import type_caster
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import type_caster_pybind11
except ImportError:
  type_caster_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (type_caster,
                                             type_caster_pybind11))
    if np[1] is not None
])
class TypeCasterTest(absltest.TestCase):

  def test_get_values(self, wrapper_lib):
    self.assertEqual(wrapper_lib.get_value_direct(10), 11)
    self.assertEqual(wrapper_lib.get_value_optional(12), 13)
    self.assertEqual(wrapper_lib.get_value_variant(14), 15)
    self.assertEqual(wrapper_lib.return_value(11), 12)
    self.assertCountEqual(
        wrapper_lib.return_value_list([11, 12, 13]), [12, 13, 14])

  def test_pyobjfrom_only(self, wrapper_lib):
    self.assertEqual(wrapper_lib.return_value_pyobjfrom_only(11), 13)

  def test_pyobjas_only(self, wrapper_lib):
    self.assertEqual(wrapper_lib.get_value_pyobjas_only(10), 13)


if __name__ == '__main__':
  absltest.main()
