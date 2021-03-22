# Lint-as: python3

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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import return_set_as_list
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import return_set_as_list_pybind11
except ImportError:
  return_set_as_list_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (return_set_as_list,
                                             return_set_as_list_pybind11))
    if np[1] is not None
])
class ReturnSetAsListTest(absltest.TestCase):

  def testGetSetString(self, wrapper_lib):
    ret = wrapper_lib.get_set_string(0)
    self.assertListEqual(ret, [])
    ret = wrapper_lib.get_set_string(1)
    self.assertListEqual(ret, ['5'])
    ret = wrapper_lib.get_set_string(3)
    self.assertListEqual(ret, ['11', '5', '8'])  # Sorted lexically.


if __name__ == '__main__':
  absltest.main()
