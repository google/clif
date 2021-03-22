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
from absl.testing import parameterized

from clif.testing.python import virtual_funcs
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import virtual_funcs_pybind11
except ImportError:
  virtual_funcs_pybind11 = None
# pylint: enable=g-import-not-at-top


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

  def __init__(self, a, b):
    super(ClassNonDefConstImpl, self).__init__(a, b)
    self.c = [1, 2, 3]  # Must have a non-trivial container to enable gc.
    # Remove self.invalidated after gaining (limited) access to invalidated ptr.
    self.invalidated = False

  def DoSomething(self):
    return -1 if self.invalidated else self.a * self.b


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (virtual_funcs,
                                             virtual_funcs_pybind11))
    if np[1] is not None
])
class VirtualTest(absltest.TestCase):

  def testInitAbstract(self, wrapper_lib):
    self.assertRaises(ValueError, wrapper_lib.K)
    self.assertRaises(ValueError, wrapper_lib.AbstractClassNonDefConst)

  def testInitConcreteClassWithVirtualMethods(self, wrapper_lib):
    b = wrapper_lib.B()
    b.set_c(2)
    self.assertEqual(b.c, 2)

    c = wrapper_lib.ClassNonDefConst(1, 2)
    self.assertEqual(c.DoSomething(), 3)

  def testBasicCall(self, wrapper_lib):
    b = B()
    b.set_c(2)
    self.assertEqual(b.c, 2)
    wrapper_lib.Bset(b, 4)
    self.assertEqual(b.c, 4)

  def testVirtual(self, wrapper_lib):
    self.assertEqual(wrapper_lib.seq(K(), 2, 6), [0, 2, 4, 6])

    abc_non_def_impl = AbstractClassNonDefConstImpl(4, 5)
    self.assertEqual(abc_non_def_impl.DoSomething(), 20)
    self.assertEqual(wrapper_lib.DoSomething1(abc_non_def_impl), 20)

    non_def_impl = ClassNonDefConstImpl(4, 5)
    self.assertEqual(non_def_impl.DoSomething(), 20)
    self.assertEqual(wrapper_lib.DoSomething2(non_def_impl), 20)

  def testVirtual2(self, wrapper_lib):
    q = L(3)
    self.assertEqual(wrapper_lib.add_seq(q, 2, 6), 3)
    self.assertEqual(q.data(), [0, 2, 4])

  def testTemporaryInstance(self, wrapper_lib):
    man = wrapper_lib.Manager(wrapper_lib.ClassNonDefConst(100, 23))
    self.assertEqual(man.DoIt(), 123)
    man = wrapper_lib.Manager(ClassNonDefConstImpl(100, 123))
    self.assertEqual(man.DoIt(), 12300)

  def testVirtualProperty(self, wrapper_lib):
    c = wrapper_lib.D()
    c.pos_c = -1
    self.assertEqual(c.pos_c, 1)

  def testNotLeakComplexPythonInstance(self, wrapper_lib):
    # Test for b/64524765. Ensure that after the Python object deleted, it's
    # not leaked. Reference to it saved during C++ virtual call.
    self.assertIsNotNone(wrapper_lib)
    non_def_impl = ClassNonDefConstImpl(4, 5)
    wr = weakref.ref(non_def_impl)
    self.assertEqual(non_def_impl.DoSomething(), 20)
    del non_def_impl
    # test non_def_impl deleted ...
    self.assertIsNone(wr())

  def testReturnsObject(self, wrapper_lib):

    class TestReturnsObjectImpl(wrapper_lib.TestReturnsObject):

      def CreateObject(self):
        return object()

    instance = TestReturnsObjectImpl()
    self.assertEqual(instance.GetRefcntOfResult(), 1)


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (virtual_funcs,
                                             virtual_funcs_pybind11))
    if np[1] is not None
])
class SmartPtrsTest(absltest.TestCase):

  def testNotShared(self, wrapper_lib):
    a = ClassNonDefConstImpl(12, 30)
    # |a| is not shared with C++. So, the call to DoUniq should invalidate it.
    a.invalidated = True
    self.assertEqual(wrapper_lib.DoUniq(a), -1)
    with self.assertRaises(ValueError):
      _ = a.a
    with self.assertRaises(ValueError):
      wrapper_lib.DoUniq(a)

  def testShared(self, wrapper_lib):
    a = ClassNonDefConstImpl(1, 23)
    b = wrapper_lib.Manager(a)
    # |a| is shared between C++ and Python. So, cannot give it to Func.
    self.assertEqual(b.DoIt(), 23)
    with self.assertRaises(ValueError):
      wrapper_lib.DoUniq(a)
    # Check |a| is intact.
    self.assertEqual(a.a, 1)

  def testSharedKeepsPyObj(self, wrapper_lib):
    a = ClassNonDefConstImpl(2, 23)
    r = weakref.ref(a)
    b = wrapper_lib.Manager(a)
    del a
    # Check |a| is intact.
    self.assertEqual(b.DoIt(), 46)
    self.assertTrue(r())
    del b
    # test |a| deleted ...
    self.assertIsNone(r())

  def testSharedFreeAfterUse(self, wrapper_lib):
    a = ClassNonDefConstImpl(2, 3)
    b = wrapper_lib.Manager(a)
    self.assertEqual(b.DoIt(), 6)
    # Remove the reference in |b|
    del b
    # We should be able to call Func again
    a.invalidated = True
    self.assertEqual(wrapper_lib.DoUniq(a), -1)
    with self.assertRaises(ValueError):
      _ = a.a


if __name__ == '__main__':
  absltest.main()
