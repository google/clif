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

from clif.testing.python import vector_const_elem_ptr


class VectorConstElemPtr(unittest.TestCase):

  def testSumElemPtr(self):
    v = [vector_const_elem_ptr.Elem(val) for val in [5, 13]]
    s = vector_const_elem_ptr.sum_elem_ptr(v)
    self.assertEqual(s, 18)

  def testProdConstElemPtr(self):
    v = [vector_const_elem_ptr.Elem(val) for val in [7, 17]]
    p = vector_const_elem_ptr.prod_const_elem_ptr(v)
    self.assertEqual(p, 119)


if __name__ == '__main__':
  unittest.main()
