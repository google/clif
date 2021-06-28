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

from clif.testing.python import type_caster_pybind11 as type_caster


class TypeCasterTest(absltest.TestCase):

  def test_get_values(self):
    self.assertEqual(type_caster.get_value_direct(10), 11)
    self.assertEqual(type_caster.get_value_optional(12), 13)
    self.assertEqual(type_caster.get_value_variant(14), 15)
    self.assertEqual(type_caster.return_value(11), 12)
    self.assertCountEqual(
        type_caster.return_value_list([11, 12, 13]), [12, 13, 14])


if __name__ == '__main__':
  absltest.main()
