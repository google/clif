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

import weakref

from absl.testing import absltest

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

  def get_a(self):
    return self.a + 1


class ClassNonDefConstImpl(virtual_funcs.ClassNonDefConst):

  def __init__(self, a, b):
    super().__init__(a, b)
    self.c = [1, 2, 3]  # Must have a non-trivial container to enable gc.
    # Remove self.invalidated after gaining (limited) access to invalidated ptr.
    self.invalidated = False

  def DoSomething(self):
    return -1 if self.invalidated else self.a * self.b


class TestRenameVirtualFunctions(virtual_funcs.TestRenameVirtualFunctions):

  def func(self):
    return 10


class VirtualTest(absltest.TestCase):

  @absltest.skipIf(
      'pybind11' in virtual_funcs.__doc__,
      'Currently pybind11 does not throw exceptions when initializing abstract'
      'classes.')
  def testInitAbstract(self):
    self.assertRaises(TypeError, virtual_funcs.K)
    self.assertRaises(TypeError, virtual_funcs.AbstractClassNonDefConst)

  def testRenameVirtualFunction(self):
    obj = TestRenameVirtualFunctions()
    self.assertEqual(virtual_funcs.CallFunc(obj), 10)

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
    self.assertEqual(abc_non_def_impl.get_a(), 5)

    non_def_impl = ClassNonDefConstImpl(4, 5)
    self.assertEqual(non_def_impl.DoSomething(), 20)
    self.assertEqual(virtual_funcs.DoSomething2(non_def_impl), 20)

  def testVirtual2(self):
    q = L(3)
    self.assertEqual(virtual_funcs.add_seq(q, 2, 6), 3)
    self.assertEqual(q.data(), [0, 2, 4])

  def testTemporaryInstance(self):
    man = virtual_funcs.Manager(virtual_funcs.ClassNonDefConst(100, 23))
    self.assertEqual(man.DoIt(), 123)
    man = virtual_funcs.Manager(ClassNonDefConstImpl(100, 123))
    self.assertEqual(man.DoIt(), 12300)

  def testVirtualProperty(self):
    c = virtual_funcs.D()
    c.pos_c = -1
    self.assertEqual(c.pos_c, 1)

  def testNotLeakComplexPythonInstance(self):
    # Test for b/64524765. Ensure that after the Python object deleted, it's
    # not leaked. Reference to it saved during C++ virtual call.
    non_def_impl = ClassNonDefConstImpl(4, 5)
    wr = weakref.ref(non_def_impl)
    self.assertEqual(non_def_impl.DoSomething(), 20)
    del non_def_impl
    # test non_def_impl deleted ...
    self.assertIsNone(wr())

  def testReturnsObject(self):

    class TestReturnsObjectImpl(virtual_funcs.TestReturnsObject):

      def CreateObject(self):
        return object()

    instance = TestReturnsObjectImpl()
    self.assertEqual(instance.GetRefcntOfResult(), 1)


class SmartPtrsTest(absltest.TestCase):

  def testNotShared(self):
    a = ClassNonDefConstImpl(12, 30)
    # |a| is not shared with C++. So, the call to DoUniq should invalidate it.
    a.invalidated = True
    self.assertEqual(virtual_funcs.DoUniq(a), -1)
    with self.assertRaises(ValueError):
      _ = a.a
    with self.assertRaises(ValueError):
      virtual_funcs.DoUniq(a)

  def testShared(self):
    a = ClassNonDefConstImpl(1, 23)
    b = virtual_funcs.Manager(a)
    # |a| is shared between C++ and Python. So, cannot give it to Func.
    self.assertEqual(b.DoIt(), 23)
    with self.assertRaises(ValueError):
      virtual_funcs.DoUniq(a)
    # Check |a| is intact.
    self.assertEqual(a.a, 1)

  def testSharedKeepsPyObj(self):
    a = ClassNonDefConstImpl(2, 23)
    r = weakref.ref(a)
    b = virtual_funcs.Manager(a)
    del a
    # Check |a| is intact.
    self.assertEqual(b.DoIt(), 46)
    self.assertTrue(r())
    del b
    # test |a| deleted ...
    self.assertIsNone(r())

  def testSharedFreeAfterUse(self):
    a = ClassNonDefConstImpl(2, 3)
    b = virtual_funcs.Manager(a)
    self.assertEqual(b.DoIt(), 6)
    # Remove the reference in |b|
    del b
    # We should be able to call Func again
    a.invalidated = True
    self.assertEqual(virtual_funcs.DoUniq(a), -1)
    with self.assertRaises(ValueError):
      _ = a.a


if __name__ == '__main__':
  absltest.main()
