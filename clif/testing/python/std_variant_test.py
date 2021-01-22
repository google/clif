"""Tests for CLIF conversion of ::std::variant."""

from absl.testing import absltest
from clif.testing.python import std_variant


class VariantClifTest(absltest.TestCase):

  def test_conversion(self):
    self.assertEqual(std_variant.index_int_str_list(10), 0)
    self.assertEqual(std_variant.index_int_str_list(-5), 0)
    self.assertEqual(std_variant.index_int_str_list("abc"), 1)
    self.assertEqual(std_variant.index_int_str_list((0, 1, 2)), 2)

    self.assertEqual(std_variant.identity_int_str_list(10), 10)
    self.assertEqual(std_variant.identity_int_str_list(-5), -5)
    self.assertEqual(std_variant.identity_int_str_list("abc"), "abc")
    # Tuple is converted to std::vector, then converted back to list, since list
    # is the default CLIF conversion type for std::vector.
    self.assertEqual(std_variant.identity_int_str_list((0, 1, 2)), [0, 1, 2])

  def test_ambiguous_conversion(self):
    # First successful conversion is used.
    self.assertEqual(std_variant.index_int_float(0), 0)
    self.assertEqual(std_variant.index_float_int(0), 0)

    self.assertIsInstance(std_variant.identity_int_float(0), int)
    self.assertIsInstance(std_variant.identity_float_int(0), float)
    self.assertIsInstance(std_variant.identity_opt_int_float(0), int)

    # Argument 0.0 is not ambiguous.
    self.assertEqual(std_variant.index_int_float(0.0), 1)
    self.assertEqual(std_variant.index_float_int(0.0), 0)

    self.assertIsInstance(std_variant.identity_int_float(0.0), float)
    self.assertIsInstance(std_variant.identity_float_int(0.0), float)
    self.assertIsInstance(std_variant.identity_opt_int_float(0.0), float)

    self.assertIsNone(std_variant.identity_opt_int_float(None))

  def test_custom_conversions(self):
    # Conversion values are +1 to ensure that custom conversions are used rather
    # than generic std::optional or std::unique_ptr conversions.
    self.assertEqual(std_variant.get_direct(1), 2)
    self.assertEqual(std_variant.get_optional(2), 3)
    self.assertEqual(std_variant.get_unique_ptr(3), 4)

  def test_error_condition(self):
    with self.assertRaises(TypeError):
      std_variant.index_int_str_list(("abc", "def"))

    with self.assertRaises(TypeError):
      std_variant.index_int_str_list(1.1)

    with self.assertRaises(TypeError):
      std_variant.get_direct(-1)

    with self.assertRaises(TypeError):
      std_variant.get_optional(-1)

    with self.assertRaises(TypeError):
      std_variant.get_unique_ptr(-1)


if __name__ == "__main__":
  absltest.main()
