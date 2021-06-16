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

from clif.testing.python import extend_classmethods
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import extend_classmethods_pybind11
except ImportError:
  extend_classmethods_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (extend_classmethods,
                                             extend_classmethods_pybind11))
    if np[1] is not None
])
class ExtendClassmethodsTest(absltest.TestCase):

  def test_create_from_value(self, wrapper_lib):
    expected_value = 543
    abc = wrapper_lib.Abc.from_value(expected_value)
    self.assertEqual(abc.get_value(), expected_value)

  def test_set_class_variable(self, wrapper_lib):
    expected_value = 5432
    wrapper_lib.Abc.set_static_value(expected_value)
    self.assertEqual(wrapper_lib.Abc.get_static_value(), expected_value)


if __name__ == '__main__':
  absltest.main()
