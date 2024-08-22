"""Contains tests for CLIF wrapped libraries that use the `interface` keyword.

This test is primarily intended to ensure that the CLIF generated C++ headers
can be properly consumed by a CLIF library that uses types declared in a
different CLIF library where the `interface` keyword is used in either module.
"""

from absl.testing import absltest

from clif.testing.python import interface_declarer
from clif.testing.python import interface_user


class InterfaceTest(absltest.TestCase):

  def test_constructible_for_int(self):
    value = interface_declarer.ValueContainerOfInt(10)
    self.assertEqual(value.GetValue(), 10)
    value.SetValue(30)
    self.assertEqual(value.GetValue(), 30)

  def test_constructible_for_float(self):
    value = interface_declarer.ValueContainerOfFloat(3.14)
    self.assertEqual(value.GetValue(), 3.14)
    value.SetValue(2.7)
    self.assertEqual(value.GetValue(), 2.7)

  def test_double_value_for_int(self):
    value = interface_user.DoubleIntValue(
        interface_declarer.ValueContainerOfInt(10)
    )
    self.assertEqual(value.GetValue(), 20)

  def test_double_value_for_float(self):
    value = interface_user.DoubleFloatValue(
        interface_declarer.ValueContainerOfFloat(3.14)
    )
    self.assertEqual(value.GetValue(), 6.28)

  def test_constructible_for_doubling_int(self):
    value = interface_user.DoublingContainerOfInt(10)
    self.assertEqual(value.GetValue(), 10)
    value.DoubleSelf()
    self.assertEqual(value.GetValue(), 20)

  def test_constructible_for_doubling_float(self):
    value = interface_user.DoublingContainerOfFloat(3.14)
    self.assertEqual(value.GetValue(), 3.14)
    value.DoubleSelf()
    self.assertEqual(value.GetValue(), 6.28)


if __name__ == "__main__":
  absltest.main()
