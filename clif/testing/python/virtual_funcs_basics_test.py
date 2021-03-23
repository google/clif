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

"""Tests for clif.testing.python.virtual_funcs_basics."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import virtual_funcs_basics
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import virtual_funcs_basics_pybind11
except ImportError:
  virtual_funcs_basics_pybind11 = None
# pylint: enable=g-import-not-at-top

HAVE_PB11 = virtual_funcs_basics_pybind11 is not None


class B(virtual_funcs_basics.B):

  def __init__(self):
    virtual_funcs_basics.B.__init__(self)
    self.c = -1

  def set_c(self, v):
    self.c = v


class BPybind11(virtual_funcs_basics_pybind11.B if HAVE_PB11 else object):

  def __init__(self):
    virtual_funcs_basics_pybind11.B.__init__(self)
    self.c = -1

  def set_c(self, v):
    self.c = v


def get_derived_b(wrapper_lib):
  return BPybind11 if wrapper_lib is virtual_funcs_basics_pybind11 else B


class K(virtual_funcs_basics.K):

  def inc(self, n):
    self.i += n


class KPybind11(virtual_funcs_basics_pybind11.K if HAVE_PB11 else object):

  def inc(self, n):
    self.i += n


def get_derived_k(wrapper_lib):
  return KPybind11 if wrapper_lib is virtual_funcs_basics_pybind11 else K


class L(virtual_funcs_basics.Q):

  def __init__(self, max_len):
    virtual_funcs_basics.Q.__init__(self)
    self._q = []
    self._max = max_len

  def data(self):
    return list(self._q)

  def PossiblyPush(self, data):
    if len(self._q) < self._max:
      self._q.append(data)
      return True
    return False


class LPybind11(virtual_funcs_basics_pybind11.Q if HAVE_PB11 else object):

  def __init__(self, max_len):
    virtual_funcs_basics_pybind11.Q.__init__(self)
    self._q = []
    self._max = max_len

  def data(self):
    return list(self._q)

  def PossiblyPush(self, data):
    if len(self._q) < self._max:
      self._q.append(data)
      return True
    return False


def get_derived_l(wrapper_lib):
  return LPybind11 if wrapper_lib is virtual_funcs_basics_pybind11 else L


class AbstractClassNonDefConstImpl(
    virtual_funcs_basics.AbstractClassNonDefConst):

  def DoSomething(self):
    return self.a * self.b


class AbstractClassNonDefConstImplPybind11(
    virtual_funcs_basics_pybind11.AbstractClassNonDefConst if HAVE_PB11 else
    object):

  def DoSomething(self):
    return self.a * self.b


def get_derived_abc_non_def_impl(wrapper_lib):
  if wrapper_lib is virtual_funcs_basics_pybind11:
    return AbstractClassNonDefConstImplPybind11
  return AbstractClassNonDefConstImpl


class ClassNonDefConstImpl(virtual_funcs_basics.ClassNonDefConst):

  def __init__(self, a, b):
    super(ClassNonDefConstImpl, self).__init__(a, b)
    self.c = [1, 2, 3]  # Must have a non-trivial container to enable gc.
    # Remove self.invalidated after gaining (limited) access to invalidated ptr.
    self.invalidated = False

  def DoSomething(self):
    return -1 if self.invalidated else self.a * self.b


class ClassNonDefConstImplPybind11(
    virtual_funcs_basics_pybind11.ClassNonDefConst if HAVE_PB11 else object):

  def __init__(self, a, b):
    super(ClassNonDefConstImplPybind11, self).__init__(a, b)
    self.c = [1, 2, 3]  # Must have a non-trivial container to enable gc.
    # Remove self.invalidated after gaining (limited) access to invalidated ptr.
    self.invalidated = False

  def DoSomething(self):
    return -1 if self.invalidated else self.a * self.b


def get_derived_non_def_impl(wrapper_lib):
  if wrapper_lib is virtual_funcs_basics_pybind11:
    return ClassNonDefConstImplPybind11
  return ClassNonDefConstImpl


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (virtual_funcs_basics,
                                             virtual_funcs_basics_pybind11))
    if np[1] is not None
])
class VirtualFuncsTest(absltest.TestCase):

  def testInitConcreteClassWithVirtualMethods(self, wrapper_lib):
    b = get_derived_b(wrapper_lib)()
    b.set_c(2)
    self.assertEqual(b.c, 2)

    c = virtual_funcs_basics.ClassNonDefConst(1, 2)
    self.assertEqual(c.DoSomething(), 3)

  def testBasicCall(self, wrapper_lib):
    b = get_derived_b(wrapper_lib)()
    b.set_c(2)
    self.assertEqual(b.c, 2)
    wrapper_lib.Bset(b, 4)
    self.assertEqual(b.c, 4)

  def testVirtual(self, wrapper_lib):
    k = get_derived_k(wrapper_lib)()
    self.assertEqual(wrapper_lib.seq(k, 2, 6), [0, 2, 4, 6])

    abc_non_def_impl = get_derived_abc_non_def_impl(wrapper_lib)(4, 5)
    self.assertEqual(abc_non_def_impl.DoSomething(), 20)
    self.assertEqual(wrapper_lib.DoSomething1(abc_non_def_impl), 20)

    non_def_impl = get_derived_non_def_impl(wrapper_lib)(4, 5)
    self.assertEqual(non_def_impl.DoSomething(), 20)
    self.assertEqual(wrapper_lib.DoSomething2(non_def_impl), 20)

  def testVirtual2(self, wrapper_lib):
    q = get_derived_l(wrapper_lib)(3)
    self.assertEqual(wrapper_lib.add_seq(q, 2, 6), 3)
    self.assertEqual(q.data(), [0, 2, 4])

  def testVirtualProperty(self, wrapper_lib):
    c = wrapper_lib.D()
    c.pos_c = -1
    self.assertEqual(c.pos_c, 1)


if __name__ == '__main__':
  absltest.main()
