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

"""Tests for clif.testing.python.classes."""

from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import classes


class ClassesTest(parameterized.TestCase):

  def testKlass(self):
    self.assertEqual(classes.Klass.C2(), 3)
    k = classes.Klass(3)
    self.assertEqual(k.i, 3)
    self.assertEqual(k.i2, 9)
    self.assertEqual(k.Int1(), 4)
    k.i = 0
    self.assertEqual(k.i, 0)
    # AttributeError on CPython; TypeError on PyPy.
    with self.assertRaises((AttributeError, TypeError)):
      k.i2 = 0

  def testMockIsRejected(self):
    k_inst = classes.Klass(3)
    self.assertEqual(classes.PassKlass(k_inst), 30)
    d_inst = classes.Derived.Init(4, 0)
    self.assertEqual(classes.PassKlass(d_inst), 40)
    with mock.patch.object(classes, 'Klass', autospec=True):
      k_mock = classes.Klass(3)
      with self.assertRaises(TypeError) as ctx:
        classes.PassKlass(k_mock)
      self.assertIn('Mock', str(ctx.exception))
    with mock.patch.object(classes, 'Derived', autospec=True):
      d_mock = classes.Derived.Init(4, 0)
      with self.assertRaises(TypeError) as ctx:
        classes.PassKlass(d_mock)
      self.assertIn('Mock', str(ctx.exception))

  def testDerivedClassDocstring(self):
    # Nothing special about this being a derived class; that is just the
    # one our test .clif file has a docstring on.
    self.assertIn('class also has a "docstring".\n\n', classes.Derived.__doc__)
    self.assertIn('spans multiple lines', classes.Derived.__doc__)
    self.assertIn(classes.Derived.__doc__, classes.Derived.__doc__.strip())

  def testPythonDerived(self):
    class PyK(classes.Klass):
      pass
    k = PyK(4)
    self.assertEqual(k.i, 4)
    self.assertEqual(k.Int1(), 5)

  def testDerived(self):
    k = classes.Derived.Init(0, 0)
    self.assertEqual(k.i, 0)
    self.assertEqual(k.j, 0)
    self.assertNotIn(2, k)
    with self.assertRaises(TypeError):
      classes.Derived(1)

  def testDerivedInit(self):
    k = classes.Derived.Init(1, 2)
    self.assertEqual(k.i, 1)
    self.assertEqual(k.j, 2)

  def testAddInit(self):
    # Test generation of default constructor
    k = classes.AddInit()
    self.assertEqual(k.i, 567483)

  def testOverloadedGetterProperty(self):
    obj = classes.OverloadedGetterProperty(10)
    self.assertEqual(obj.x, 10)

  def testBytesAttributes(self):
    obj = classes.BytesAttributes('str_readonly')
    obj.str_as_bytes = 'str_as_bytes'
    self.assertEqual(obj.str_as_bytes, b'str_as_bytes')
    obj.str_as_bytes = b'str_as_bytes123'
    self.assertEqual(obj.str_as_bytes, b'str_as_bytes123')
    obj.str_as_str = 'str_as_str'
    self.assertEqual(obj.str_as_str, 'str_as_str')
    obj.str_as_str = b'str_as_str123'
    self.assertEqual(obj.str_as_str, 'str_as_str123')
    self.assertEqual(obj.str_readonly, b'str_readonly')
    obj.str_readwrite = 'str_readwrite'
    self.assertEqual(obj.str_readwrite, b'str_readwrite')

  def testIgnoreDefaultCtor(self):
    with self.assertRaises((ValueError, TypeError)):
      classes.NoDefaultConstructor()

  def testGenerateDefaultCtor(self):
    obj = classes.AddInitNoParams.Init()
    self.assertEqual(obj.get_value(), 10)
    obj = classes.AddInitNoParams()
    self.assertEqual(obj.get_value(), 10)

  def testHandleAmbiguousNamespace(self):
    obj = classes.WithAmbiguousNamespace()
    self.assertEqual(obj.get_value(), 10)

  @parameterized.parameters(
      ('pair_attr_str_str', ('foo', 'bar'), ('foo1', 'bar1'), ('foo1', 'bar1')),
      (
          'pair_attr_str_bytes',
          ('foo', b'bar'),
          ('foo1', 'bar1'),
          ('foo1', b'bar1'),
      ),
      (
          'pair_attr_bytes_str',
          (b'foo', 'bar'),
          ('foo1', 'bar1'),
          (b'foo1', 'bar1'),
      ),
      (
          'pair_attr_bytes_bytes',
          (b'foo', b'bar'),
          ('foo1', 'bar1'),
          (b'foo1', b'bar1'),
      ),
      (
          'pair_property_str_str',
          ('foo', 'bar'),
          ('foo1', 'bar1'),
          ('foo1', 'bar1'),
      ),
      (
          'pair_property_str_bytes',
          ('foo', b'bar'),
          ('foo1', 'bar1'),
          ('foo1', b'bar1'),
      ),
      (
          'pair_property_bytes_str',
          (b'foo', 'bar'),
          ('foo1', 'bar1'),
          (b'foo1', 'bar1'),
      ),
      (
          'pair_property_bytes_bytes',
          (b'foo', b'bar'),
          ('foo1', 'bar1'),
          (b'foo1', b'bar1'),
      ),
  )
  def testNestedAttributes(self, attr, expected, new_value, new_expected):
    obj = classes.NestedAttributes()
    ret = getattr(obj, attr)
    self.assertEqual(ret, expected)
    setattr(obj, attr, new_value)
    ret = getattr(obj, attr)
    self.assertEqual(ret, new_expected)

  @parameterized.parameters(
      (
          'pair_unproperty_str_str',
          ('foo', 'bar'),
          ('foo1', 'bar1'),
          ('foo1', 'bar1'),
      ),
      (
          'pair_unproperty_str_bytes',
          ('foo', b'bar'),
          ('foo1', 'bar1'),
          ('foo1', b'bar1'),
      ),
      (
          'pair_unproperty_bytes_str',
          (b'foo', 'bar'),
          ('foo1', 'bar1'),
          (b'foo1', 'bar1'),
      ),
      (
          'pair_unproperty_bytes_bytes',
          (b'foo', b'bar'),
          ('foo1', 'bar1'),
          (b'foo1', b'bar1'),
      ),
  )
  def testNestedUnproperty(self, attr, expected, new_value, new_expected):
    getter = 'get_' + attr
    setter = 'set_' + attr
    obj = classes.NestedAttributes()
    ret = getattr(obj, getter)()
    self.assertEqual(ret, expected)
    getattr(obj, setter)(new_value)
    ret = getattr(obj, getter)()
    self.assertEqual(ret, new_expected)


if __name__ == '__main__':
  absltest.main()
