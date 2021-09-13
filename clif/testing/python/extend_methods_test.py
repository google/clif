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

from absl.testing import absltest

from clif.python import type_customization
from clif.testing.python import extend_methods


def DirectlyAssigned(self, prefix):
  return prefix.upper() + self.__class__.__name__


# Direct assignment for unit test, NOT recommended for general use.
extend_methods.ConcreteHolder.DirectlyAssigned = DirectlyAssigned
extend_methods.VirtualBaseHolder.DirectlyAssigned = DirectlyAssigned


# RECOMMENDED for general use.
@type_customization.extend(extend_methods.ConcreteHolder)
class _:
  """Added to ConcreteHolder."""

  data = 'Data added to ConcreteHolder.'

  def AnInstanceMethod(self, prefix):
    return ':'.join((prefix.upper(), 'self', self.__class__.__name__))

  @classmethod
  def AClassMethod(cls, prefix):
    return ':'.join((prefix.lower(), 'cls', cls.__name__))

  @staticmethod
  def AStaticMethod(prefix):
    return ':'.join((prefix.capitalize(), 'static'))

  @property
  def a_property(self):
    return ':'.join(('getter', str(self.Get()), self.__class__.__name__))

  @a_property.setter
  def a_property(self, value):
    self.Set(value + 5)


@type_customization.extend(extend_methods.VirtualBaseHolder)
class _:
  data = 'Data added to VirtualBaseHolder.'

  def AnInstanceMethod(self, prefix):
    return ':'.join((prefix.capitalize(), 'self', self.__class__.__name__))

  @classmethod
  def AClassMethod(cls, prefix):
    return ':'.join((prefix.upper(), 'cls', cls.__name__))

  @staticmethod
  def AStaticMethod(prefix):
    return ':'.join((prefix.lower(), 'static'))

  @property
  def a_property(self):
    return ':'.join(('Getter', str(self.Get()), self.__class__.__name__))

  @a_property.setter
  def a_property(self, value):
    self.Set(value + 7)


@type_customization.extend(extend_methods.VirtualBaseHolder)
class _(object):
  """Added to VirtualBaseHolder."""


@type_customization.extend(extend_methods.ConcreteHolder)
class NamedFromClass(object):

  def NfcInstanceMethod(self, prefix):
    return ':'.join(
        (''.join(reversed(prefix)), 'self', self.__class__.__name__))

  @classmethod
  def NfcClassMethod(cls, prefix):
    return ':'.join((''.join(reversed(prefix)), 'cls', cls.__name__))

  @staticmethod
  def NfcStaticMethod(prefix):
    return ':'.join((''.join(reversed(prefix)), 'static'))

  @property
  def nfc_property(self):
    return ':'.join(('GETTER', str(self.Get()), self.__class__.__name__))

  @nfc_property.setter
  def nfc_property(self, value):
    self.Set(value + 11)


class NfcInstanceMethodOverride(object):

  def NfcInstanceMethod(self, prefix):
    return ':'.join(
        (''.join(reversed(prefix)).upper(), 'self', self.__class__.__name__))


# Re-use with override.
@type_customization.extend(extend_methods.VirtualBaseHolder)
class _(NfcInstanceMethodOverride, NamedFromClass):
  pass


# Keeping the failure tests below at module scope (not inside test methods)
# because this is more representative of the actual (invalid) use cases.

try:
  @type_customization.extend(extend_methods.ConcreteHolder)
  class _:
    pass
except TypeError as e:
  _from_class_old_style_failure_test_error = str(e)
else:
  _from_class_old_style_failure_test_error = None


class _BaseOldStyleFailureTestBase:  # Python 2 old-style.
  pass


try:
  @type_customization.extend(extend_methods.ConcreteHolder)
  class _(_BaseOldStyleFailureTestBase, object):
    pass
except TypeError as e:
  _base_old_style_failure_test_error = str(e)
else:
  _base_old_style_failure_test_error = None


class _BaseBaseFailureTestBase(object):
  pass


class _BaseBaseFailureTestDerived(_BaseBaseFailureTestBase):
  pass


try:
  @type_customization.extend(extend_methods.ConcreteHolder)
  class _(_BaseBaseFailureTestDerived):
    pass
except TypeError as e:
  _base_base_failure_test_error = str(e)
else:
  _base_base_failure_test_error = None


try:
  @type_customization.extend(extend_methods.ConcreteHolder)
  class _(tuple):  # Any type exercising rejection of __getattribute__.
    pass
except TypeError as e:
  _tuple_as_base_failure_test_error = str(e)
else:
  _tuple_as_base_failure_test_error = None


class ExtendMethodsTest(absltest.TestCase):

  def testConcreteDirectAssignment(self):
    ch = extend_methods.ConcreteHolder()
    s = ch.DirectlyAssigned('Red:')
    self.assertEqual(s, 'RED:ConcreteHolder')

  def testVirtualDirectAssignment(self):
    vdh = extend_methods.VirtualDerivedHolder()
    s = vdh.DirectlyAssigned('Blue:')
    self.assertEqual(s, 'BLUE:VirtualDerivedHolder')

  def testConcreteExtend(self):
    expected_doc = 'Added to ConcreteHolder.'
    self.assertEqual(extend_methods.ConcreteHolder.__doc__, expected_doc)
    self.assertEqual(
        extend_methods.ConcreteHolder.data,
        'Data added to ConcreteHolder.')
    ch = extend_methods.ConcreteHolder()
    s = ch.AnInstanceMethod('Green')
    self.assertEqual(s, 'GREEN:self:ConcreteHolder')
    s = ch.AClassMethod('Yellow')
    self.assertEqual(s, 'yellow:cls:ConcreteHolder')
    s = extend_methods.ConcreteHolder.AClassMethod('Gray')
    self.assertEqual(s, 'gray:cls:ConcreteHolder')
    s = ch.AStaticMethod('magenta')
    self.assertEqual(s, 'Magenta:static')
    s = extend_methods.ConcreteHolder.AStaticMethod('silver')
    self.assertEqual(s, 'Silver:static')
    s = ch.a_property
    self.assertEqual(s, 'getter:0:ConcreteHolder')
    ch.a_property = 13
    s = ch.a_property
    self.assertEqual(s, 'getter:18:ConcreteHolder')

  def testVirtualExtend(self):
    if 'pybind11' not in extend_methods.__doc__:
      expected_doc = 'Added to VirtualBaseHolder.'
      self.assertEqual(extend_methods.VirtualBaseHolder.__doc__, expected_doc)
      self.assertEqual(extend_methods.VirtualDerivedHolder.__doc__,
                       'CLIF wrapper for ::clif_testing::VirtualDerivedHolder')
    self.assertEqual(
        extend_methods.VirtualBaseHolder.data,
        'Data added to VirtualBaseHolder.')
    self.assertEqual(
        extend_methods.VirtualDerivedHolder.data,
        'Data added to VirtualBaseHolder.')
    vdh = extend_methods.VirtualDerivedHolder()
    s = vdh.AnInstanceMethod('orange')
    self.assertEqual(s, 'Orange:self:VirtualDerivedHolder')
    s = vdh.AClassMethod('Purple')
    self.assertEqual(s, 'PURPLE:cls:VirtualDerivedHolder')
    s = extend_methods.VirtualBaseHolder.AClassMethod('Cyan')
    self.assertEqual(s, 'CYAN:cls:VirtualBaseHolder')
    s = extend_methods.VirtualDerivedHolder.AClassMethod('Mint')
    self.assertEqual(s, 'MINT:cls:VirtualDerivedHolder')
    s = vdh.AStaticMethod('Black')
    self.assertEqual(s, 'black:static')
    s = extend_methods.VirtualBaseHolder.AStaticMethod('Gold')
    self.assertEqual(s, 'gold:static')
    s = extend_methods.VirtualDerivedHolder.AStaticMethod('Platinum')
    self.assertEqual(s, 'platinum:static')
    s = vdh.a_property
    self.assertEqual(s, 'Getter:0:VirtualDerivedHolder')
    vdh.a_property = 29
    s = vdh.a_property
    self.assertEqual(s, 'Getter:36:VirtualDerivedHolder')

  def testNamedFromClass(self):
    nfc = NamedFromClass()
    ch = extend_methods.ConcreteHolder()
    vdh = extend_methods.VirtualDerivedHolder()

    s = nfc.NfcInstanceMethod('eeffoc')
    self.assertEqual(s, 'coffee:self:NamedFromClass')
    s = ch.NfcInstanceMethod('eeffoC')
    self.assertEqual(s, 'Coffee:self:ConcreteHolder')
    s = vdh.NfcInstanceMethod('eeffoc')
    self.assertEqual(s, 'COFFEE:self:VirtualDerivedHolder')

    s = nfc.NfcClassMethod('ynobe')
    self.assertEqual(s, 'ebony:cls:NamedFromClass')
    s = NamedFromClass.NfcClassMethod('yrovI')
    self.assertEqual(s, 'Ivory:cls:NamedFromClass')
    s = ch.NfcClassMethod('ynobE')
    self.assertEqual(s, 'Ebony:cls:ConcreteHolder')
    s = extend_methods.ConcreteHolder.NfcClassMethod('yrovi')
    self.assertEqual(s, 'ivory:cls:ConcreteHolder')
    s = vdh.NfcClassMethod('YNOBE')
    self.assertEqual(s, 'EBONY:cls:VirtualDerivedHolder')
    s = extend_methods.VirtualDerivedHolder.NfcClassMethod('YROVI')
    self.assertEqual(s, 'IVORY:cls:VirtualDerivedHolder')

    s = NamedFromClass.NfcStaticMethod('doow')
    self.assertEqual(s, 'wood:static')
    s = extend_methods.ConcreteHolder.NfcStaticMethod('dooW')
    self.assertEqual(s, 'Wood:static')
    s = extend_methods.VirtualDerivedHolder.NfcStaticMethod('DOOW')
    self.assertEqual(s, 'WOOD:static')

    with self.assertRaises(AttributeError) as ctx:
      nfc.nfc_property  # pylint: disable=pointless-statement
    self.assertEqual(
        str(ctx.exception), "'NamedFromClass' object has no attribute 'Get'")
    with self.assertRaises(AttributeError) as ctx:
      nfc.nfc_property = 0
    self.assertEqual(
        str(ctx.exception), "'NamedFromClass' object has no attribute 'Set'")

    s = ch.nfc_property
    self.assertEqual(s, 'GETTER:0:ConcreteHolder')
    ch.nfc_property = 59
    s = ch.nfc_property
    self.assertEqual(s, 'GETTER:70:ConcreteHolder')
    s = vdh.nfc_property
    self.assertEqual(s, 'GETTER:0:VirtualDerivedHolder')
    vdh.nfc_property = 71
    s = vdh.nfc_property
    self.assertEqual(s, 'GETTER:82:VirtualDerivedHolder')

  def testFromClassOldStyleFailureTestError(self):
    self.assertIsNone(_from_class_old_style_failure_test_error)

  def testBaseOldStyleFailureTestError(self):
    self.assertIsNone(_base_old_style_failure_test_error)

  def testBaseBaseFailureTestError(self):
    self.assertIsNotNone(_base_base_failure_test_error)
    self.assertIn('extend from_class base ', _base_base_failure_test_error)
    self.assertIn(
        ' must not have bases themselves ', _base_base_failure_test_error)
    self.assertIn('BaseBaseFailureTestDerived', _base_base_failure_test_error)
    self.assertIn('BaseBaseFailureTestBase', _base_base_failure_test_error)

  def testTupleAsBaseFailureTestError(self):
    self.assertIn(
        'extend base must not have a __getattribute__ attribute (base ',
        _tuple_as_base_failure_test_error)
    self.assertIn(' does).', _tuple_as_base_failure_test_error)
    self.assertIn('tuple', _tuple_as_base_failure_test_error)


if __name__ == '__main__':
  absltest.main()
