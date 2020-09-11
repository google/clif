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

import unittest

from clif.testing.python import pass_none


class ExtendMethodsTest(unittest.TestCase):

  def testPassByValue(self):
    ih = pass_none.IntHolder(29)
    res = pass_none.pass_holder_by_value(ih)
    self.assertEqual(res, 87)
    with self.assertRaises(TypeError) as ctx:
      pass_none.pass_holder_by_value(None)
    self.assertEqual(
        str(ctx.exception),
        'pass_holder_by_value() argument holder is not valid for'
        ' ::clif_testing::IntHolder (NoneType instance given)')

  def testPassConstRefHolder(self):
    ih = pass_none.IntHolder(37)
    res = pass_none.pass_const_ref_holder(ih)
    self.assertEqual(res, 185)
    with self.assertRaises(TypeError) as ctx:
      pass_none.pass_const_ref_holder(None)
    self.assertEqual(
        str(ctx.exception),
        'pass_const_ref_holder() argument holder is not valid for'
        ' ::clif_testing::IntHolder (NoneType instance given)')

  def testPassConstPtrHolder(self):
    ih = pass_none.IntHolder(41)
    res = pass_none.pass_const_ptr_holder(ih)
    self.assertEqual(res, 287)
    res = pass_none.pass_const_ptr_holder(None)
    self.assertEqual(res, 11)

  def testPassSharedPtrHolder(self):
    ih = pass_none.IntHolder(43)
    res = pass_none.pass_shared_ptr_holder(ih)
    self.assertEqual(res, 559)
    # Potential Feature Request: support shared_ptr from None.
    with self.assertRaises(TypeError) as ctx:
      pass_none.pass_shared_ptr_holder(None)
    self.assertEqual(
        str(ctx.exception),
        'pass_shared_ptr_holder() argument holder is not valid for'
        ' ::std::shared_ptr<::clif_testing::IntHolder>'
        ' (NoneType instance given): expecting'
        ' clif.testing.python.pass_none.IntHolder'
        ' instance, got NoneType instance')


if __name__ == '__main__':
  unittest.main()
