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

from clif.testing.python import pass_none
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import pass_none_pybind11
except ImportError:
  pass_none_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (pass_none, pass_none_pybind11))
    if np[1] is not None
])
class ExtendMethodsTest(absltest.TestCase):

  def testPassByValue(self, wrapper_lib):
    ih = wrapper_lib.IntHolder(29)
    res = wrapper_lib.pass_holder_by_value(ih)
    self.assertEqual(res, 87)
    with self.assertRaises(TypeError) as ctx:
      wrapper_lib.pass_holder_by_value(None)
    self.assertEqual(
        str(ctx.exception),
        'pass_holder_by_value() argument holder is not valid for'
        ' ::clif_testing::IntHolder (NoneType instance given)')

  def testPassConstRefHolder(self, wrapper_lib):
    ih = wrapper_lib.IntHolder(37)
    res = wrapper_lib.pass_const_ref_holder(ih)
    self.assertEqual(res, 185)
    with self.assertRaises(TypeError) as ctx:
      wrapper_lib.pass_const_ref_holder(None)
    self.assertEqual(
        str(ctx.exception),
        'pass_const_ref_holder() argument holder is not valid for'
        ' ::clif_testing::IntHolder (NoneType instance given)')

  def testPassConstPtrHolder(self, wrapper_lib):
    ih = wrapper_lib.IntHolder(41)
    res = wrapper_lib.pass_const_ptr_holder(ih)
    self.assertEqual(res, 287)
    res = wrapper_lib.pass_const_ptr_holder(None)
    self.assertEqual(res, 11)

  def testPassSharedPtrHolder(self, wrapper_lib):
    ih = wrapper_lib.IntHolder(43)
    res = wrapper_lib.pass_shared_ptr_holder(ih)
    self.assertEqual(res, 559)
    # Potential Feature Request: support shared_ptr from None.
    with self.assertRaises(TypeError) as ctx:
      wrapper_lib.pass_shared_ptr_holder(None)
    self.assertEqual(
        str(ctx.exception),
        'pass_shared_ptr_holder() argument holder is not valid for'
        ' ::std::shared_ptr<::clif_testing::IntHolder>'
        ' (NoneType instance given): expecting'
        ' clif.testing.python.pass_none.IntHolder'
        ' instance, got NoneType instance')


if __name__ == '__main__':
  absltest.main()
