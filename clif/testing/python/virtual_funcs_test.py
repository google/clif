# Copyright 2017 Google Inc.
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

"""Tests for clif.testing.python.virtual_funcs."""

import unittest
from clif.testing.python import virtual_funcs


class B(virtual_funcs.B):

  def __init__(self):
    virtual_funcs.B.__init__(self)
    self.c = -1

  def set_c(self, v):
    self.c = v


class K(virtual_funcs.K):

  def inc(self, n):
    self.i += n


class L(virtual_funcs.Q):

  def __init__(self, max_len):
    virtual_funcs.Q.__init__(self)
    self._q = []
    self._max = max_len

  def data(self):
    return list(self._q)

  def PossiblyPush(self, data):
    if len(self._q) < self._max:
      self._q.append(data)
      return True
    return False


class AbstractClassNonDefConstImpl(virtual_funcs.AbstractClassNonDefConst):

  def DoSomething(self):
    return self.a * self.b


class ClassNonDefConstImpl(virtual_funcs.ClassNonDefConst):

  def DoSomething(self):
    return self.a * self.b


class VirtualTest(unittest.TestCase):

  def testInitAbstract(self):
    self.assertRaises(ValueError, virtual_funcs.K)
    self.assertRaises(ValueError, virtual_funcs.AbstractClassNonDefConst)

  def testInitConcreteClassWithVirtualMethods(self):
    b = virtual_funcs.B()
    b.set_c(2)
    self.assertEqual(b.c, 2)

    c = virtual_funcs.ClassNonDefConst(1, 2)
    self.assertEqual(c.DoSomething(), 3)

  def testBasicCall(self):
    b = B()
    b.set_c(2)
    self.assertEqual(b.c, 2)
    virtual_funcs.Bset(b, 4)
    self.assertEqual(b.c, 4)

  def testVirtual(self):
    self.assertEqual(virtual_funcs.seq(K(), 2, 6), [0, 2, 4, 6])

    abc_non_def_impl = AbstractClassNonDefConstImpl(4, 5)
    self.assertEqual(abc_non_def_impl.DoSomething(), 20)
    self.assertEqual(virtual_funcs.DoSomething1(abc_non_def_impl), 20)

    non_def_impl = ClassNonDefConstImpl(4, 5)
    self.assertEqual(non_def_impl.DoSomething(), 20)
    self.assertEqual(virtual_funcs.DoSomething2(non_def_impl), 20)

  def testVirtual2(self):
    q = L(3)
    self.assertEqual(virtual_funcs.add_seq(q, 2, 6), 3)
    self.assertEqual(q.data(), [0, 2, 4])


if __name__ == '__main__':
  unittest.main()
