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

"""Tests for clif.pybind11.staging.extend_from_clifaux.

This file is a copy of
clif/testing/python/extend_from_clifaux_test.py.
"""

import unittest
from clif.pybind11.staging import extend_from_clifaux


class ExtendFromClifauxTest(unittest.TestCase):

  def testVoidSelf(self):
    wh = extend_from_clifaux.WhatHappened()
    self.assertEqual(wh.Last(), 'Nothing yet.')
    self.assertIsNone(wh.void_raw_ptr())
    self.assertEqual(wh.Last(), '* -> void')
    self.assertIsNone(wh.void_shared_ptr())
    self.assertEqual(wh.Last(), 'shared_ptr -> void')
    wh.Record('flush')
    self.assertIsNone(wh.void_by_value())
    self.assertEqual(wh.Last(), 'flush')
    self.assertIsNone(wh.void_cref())
    self.assertEqual(wh.Last(), 'const& -> void')
    self.assertIsNone(wh.void_ref())
    self.assertEqual(wh.Last(), '& -> void')

  def testIntSelf(self):
    wh = extend_from_clifaux.WhatHappened()
    self.assertEqual(wh.int_raw_ptr(), 1)
    self.assertEqual(wh.Last(), '* -> int')
    self.assertEqual(wh.int_shared_ptr(), 2)
    self.assertEqual(wh.Last(), 'shared_ptr -> int')
    wh.Record('flush')
    self.assertEqual(wh.int_by_value(), 3)
    self.assertEqual(wh.Last(), 'flush')
    self.assertEqual(wh.int_cref(), 4)
    self.assertEqual(wh.Last(), 'const& -> int')
    self.assertEqual(wh.int_ref(), 5)
    self.assertEqual(wh.Last(), '& -> int')

  def testVoidSelfInt(self):
    wh = extend_from_clifaux.WhatHappened()
    self.assertIsNone(wh.void_raw_ptr_int(1))
    self.assertEqual(wh.Last(), '*, 1 -> void')
    self.assertIsNone(wh.void_shared_ptr_int(2))
    self.assertEqual(wh.Last(), 'shared_ptr, 2 -> void')
    wh.Record('flush')
    self.assertIsNone(wh.void_by_value_int(3))
    self.assertEqual(wh.Last(), 'flush')
    self.assertIsNone(wh.void_cref_int(4))
    self.assertEqual(wh.Last(), 'const&, 4 -> void')
    self.assertIsNone(wh.void_ref_int(5))
    self.assertEqual(wh.Last(), '&, 5 -> void')

  def testIntSelfInt(self):
    wh = extend_from_clifaux.WhatHappened()
    self.assertEqual(wh.int_raw_ptr_int(-1), 1)
    self.assertEqual(wh.Last(), '*, -1 -> int')
    self.assertEqual(wh.int_shared_ptr_int(-2), 2)
    self.assertEqual(wh.Last(), 'shared_ptr, -2 -> int')
    wh.Record('flush')
    self.assertEqual(wh.int_by_value_int(-3), 3)
    self.assertEqual(wh.Last(), 'flush')
    self.assertEqual(wh.int_cref_int(-4), 4)
    self.assertEqual(wh.Last(), 'const&, -4 -> int')
    self.assertEqual(wh.int_ref_int(-5), 5)
    self.assertEqual(wh.Last(), '&, -5 -> int')

  def testIntSelfIntInt(self):
    wh = extend_from_clifaux.WhatHappened()
    self.assertEqual(wh.int_raw_ptr_int_int(10, -1), 1)
    self.assertEqual(wh.Last(), '*, 9 -> int')
    self.assertEqual(wh.int_shared_ptr_int_int(20, -2), 2)
    self.assertEqual(wh.Last(), 'shared_ptr, 18 -> int')
    wh.Record('flush')
    self.assertEqual(wh.int_by_value_int_int(30, -3), 3)
    self.assertEqual(wh.Last(), 'flush')
    self.assertEqual(wh.int_cref_int_int(40, -4), 4)
    self.assertEqual(wh.Last(), 'const&, 36 -> int')
    self.assertEqual(wh.int_ref_int_int(50, -5), 5)
    self.assertEqual(wh.Last(), '&, 45 -> int')

  def testCustomCppName(self):
    wh = extend_from_clifaux.WhatHappened()
    self.assertEqual(wh.chosen_method_name(60, -6), 6)
    self.assertEqual(wh.Last(), 'custom_function_name(*, 54) -> int')
    self.assertEqual(wh.ns_down_method(70, -7), 7)
    self.assertEqual(wh.Last(), 'ns_down::function(*, 63) -> int')
    self.assertEqual(wh.ns_up_method(80, -8), 8)
    self.assertEqual(wh.Last(), 'ns_up_function(*, 72) -> int')

  def testRenamedForPython(self):
    rfp = extend_from_clifaux.RenamedForPython()
    self.assertEqual(rfp.int_raw_ptr_int_int(100, -1), 11)
    self.assertEqual(rfp.Last(), 'ToBeRenamed*, 99 -> int')
    self.assertEqual(rfp.chosen_method_name(110, -2), 12)
    self.assertEqual(
        rfp.Last(), 'tbr_custom_function_name(ToBeRenamed*, 108) -> int')
    self.assertEqual(rfp.ns_down_method(120, -3), 13)
    self.assertEqual(
        rfp.Last(), 'ns_down::tbr_function(ToBeRenamed*, 117) -> int')


if __name__ == '__main__':
  unittest.main()
