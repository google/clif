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

from clif.testing.python import virtual_funcs_basics


class B(virtual_funcs_basics.B):

  def __init__(self):
    virtual_funcs_basics.B.__init__(self)
    self.c = -1

  def set_c(self, v):
    self.c = v


class K(virtual_funcs_basics.K):

  def inc(self, n):
    self.i += n


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


class AbstractClassNonDefConstImpl(
    virtual_funcs_basics.AbstractClassNonDefConst):

  def DoSomething(self):
    return self.a * self.b


class ClassNonDefConstImpl(virtual_funcs_basics.ClassNonDefConst):

  def __init__(self, a, b):
    super(ClassNonDefConstImpl, self).__init__(a, b)
    self.c = [1, 2, 3]  # Must have a non-trivial container to enable gc.
    # Remove self.invalidated after gaining (limited) access to invalidated ptr.
    self.invalidated = False

  def DoSomething(self):
    return -1 if self.invalidated else self.a * self.b


class VirtualFuncsTest(absltest.TestCase):

  def testInitConcreteClassWithVirtualMethods(self):
    b = B()
    b.set_c(2)
    self.assertEqual(b.c, 2)

    c = virtual_funcs_basics.ClassNonDefConst(1, 2)
    self.assertEqual(c.DoSomething(), 3)

  def testBasicCall(self):
    b = B()
    b.set_c(2)
    self.assertEqual(b.c, 2)
    virtual_funcs_basics.Bset(b, 4)
    self.assertEqual(b.c, 4)

  def testVirtual(self):
    k = K()
    self.assertEqual(virtual_funcs_basics.seq(k, 2, 6), [0, 2, 4, 6])

    abc_non_def_impl = AbstractClassNonDefConstImpl(4, 5)
    self.assertEqual(abc_non_def_impl.DoSomething(), 20)
    self.assertEqual(virtual_funcs_basics.DoSomething1(abc_non_def_impl), 20)

    non_def_impl = ClassNonDefConstImpl(4, 5)
    self.assertEqual(non_def_impl.DoSomething(), 20)
    self.assertEqual(virtual_funcs_basics.DoSomething2(non_def_impl), 20)

  def testVirtual2(self):
    q = L(3)
    self.assertEqual(virtual_funcs_basics.add_seq(q, 2, 6), 3)
    self.assertEqual(q.data(), [0, 2, 4])

  def testVirtualProperty(self):
    c = virtual_funcs_basics.D()
    c.pos_c = -1
    self.assertEqual(c.pos_c, 1)


if __name__ == '__main__':
  absltest.main()
