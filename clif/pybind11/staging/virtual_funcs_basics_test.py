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

"""Tests for clif.pybind11.staging.virtual_funcs_basics.

This file is a copy of clif/testing/python/virtual_funcs_basics_test.py.
"""

import unittest
from clif.pybind11.staging import virtual_funcs_basics


class B(virtual_funcs_basics.B):

  def __init__(self):
    virtual_funcs_basics.B.__init__(self)
    self.c = -1

  def set_c(self, v):
    self.c = v


class VirtualFuncsTest(unittest.TestCase):

  def testBasicCall(self):
    b = B()
    b.set_c(2)
    self.assertEqual(b.c, 2)
    virtual_funcs_basics.Bset(b, 4)
    self.assertEqual(b.c, 4)

  def testVirtualProperty(self):
    c = virtual_funcs_basics.D()
    c.pos_c = -1
    self.assertEqual(c.pos_c, 1)


if __name__ == '__main__':
  unittest.main()
