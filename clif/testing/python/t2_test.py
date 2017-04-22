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

"""Tests for clif.testing.t2."""

import unittest
from clif.testing.python import t2


class PyK(t2.Klass):
  pass


# This is intentionally old-style. pylint: disable=old-style-class
class OldStyleClass:
  pass


class T2Test(unittest.TestCase):

  def testKlass(self):
    self.assertEqual(t2.Klass.C2(), 3)
    k = t2.Klass(3)
    self.assertEqual(k.i, 3)
    self.assertEqual(k.i2, 9)
    self.assertEqual(k.Int1(), 4)
    self.assertIs(False, t2.k_check(k))
    with self.assertRaises(TypeError):
      t2.k_check(0)
    k.i = 0
    self.assertIs(True, t2.k_check(k))
    # AttributeError on CPython; TypeError on PyPy.
    with self.assertRaises((AttributeError, TypeError)):
      k.i2 = 0
    t2.k_modify(k, 5)
    self.assertEqual(k.i, 5)

  def testPythonDerived(self):
    k = PyK(4)
    self.assertEqual(k.i, 4)
    self.assertEqual(k.Int1(), 5)

  def testDerived(self):
    k = t2.Derived()
    self.assertEqual(k.i, 0)
    self.assertEqual(k.j, 0)
    self.assertIs(True, t2.k_check(k))
    self.assertNotIn(2, k)
    with self.assertRaises(TypeError):
      t2.Derived(1)

  def testDerivedInit(self):
    k = t2.Derived.Init(1, 2)
    self.assertEqual(k.i, 1)
    self.assertEqual(k.j, 2)
    self.assertIs(False, t2.k_check(k))

  def testAbstract(self):
    self.assertTrue(t2.Abstract.Future)
    self.assertRaises(ValueError, t2.Abstract)
    self.assertEqual(t2.Abstract.KIND, 'pure virtual',
                     str(type(t2.Abstract.KIND)))

  def testInconstructibleStaticMethod(self):
    self.assertEqual(t2.InconstructibleF(), 0)

  def testNoDefaultConstructor(self):
    with self.assertRaises(ValueError):
      # true error, no def ctor
      self.assertEqual(t2.NoDefaultConstructor().a, 1)
    with self.assertRaises(ValueError):
      # true error, non-def ctor not wrapped
      self.assertEqual(t2.NoDefaultConstructor(1).a, 1)

  # This test works as expected when the "user error" in .clif is fixed.
  # def testExplicitConstructor(self):
  #   self.assertEqual(t2.NoDefaultConstructor(1).a, 1)

  def testContextManager(self):
    self.assertEqual(t2.CtxMgr().state, t2.CtxMgr.State.UNDEFINED)
    with t2.CtxMgr() as c:
      self.assertIsNotNone(c)
      self.assertEqual(c.state, c.State.LOCKED)
    self.assertEqual(c.state, c.State.UNLOCKED)
    with self.assertRaises(ValueError):
      with t2.CtxMgr():
        raise ValueError()

  def testVectorUniq(self):
    self.assertEqual(t2.vector_inside_unique_ptr(), [])
    vs = t2.all_nocopy_holds()
    self.assertEqual(len(vs), 3)
    for actual, expected in zip(vs, [1, 2, 3]):
      self.assertIsInstance(actual, t2.NoCopy)
      self.assertEqual(actual.a, expected)

  def testVarGetSet(self):
    n = t2.Nested()
    i = n.get_i()
    i.a = 3
    n.set_i(i)
    self.assertEqual(n.get_i().a, 3)
    # Mutating an object returned by get_i does nothing as it's only a copy.
    n.get_i().a += 1
    self.assertEqual(n.get_i().a, 3)

  def test_setting_nested_container_attribute_persists(self):
    nca = t2.NestedContainerAttributes()
    nca.int_set_vector = [{1}, {2}, {3}]
    self.assertEqual(nca.int_set_vector, [{1}, {2}, {3}])

  def test_setting_nested_container_attribute_overwrites(self):
    nca = t2.NestedContainerAttributes()
    nca.int_set_vector = [{1}, {2}, {3}]
    nca.int_set_vector = [{4}]
    self.assertEqual(nca.int_set_vector, [{4}])

  def test_mutating_nested_container_attribute_does_not_persist(self):
    nca = t2.NestedContainerAttributes()
    nca.int_set_vector.append({1})
    self.assertEqual(nca.int_set_vector, [])

  def test_class_name(self):
    with self.assertRaisesRegexp(TypeError, r'\bOldStyleClass\b'):
      t2.k_check(OldStyleClass())

  def testReturnNoDefaultConstructor(self):
    self.assertIsInstance(t2.make_ndefctor(1), t2.NoDefaultConstructor)


if __name__ == '__main__':
  unittest.main()
