# Copyright 2021 Google LLC
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
from absl.testing import parameterized

# Register the classes so that pybind11 knows how to convert them from Python
# to C++.
# pylint: disable=unused-import
from clif.testing.python import lambda_expressions
# pylint: enable=unused-import
from clif.testing.python import type_caster


# For use as a temporary user-defined object, to maximize sensitivity of the
# tests below.
class PyValueHolder:

  def __init__(self, value):
    self.value = value


class TypeCasterTest(parameterized.TestCase):

  def test_get_values(self):
    self.assertEqual(type_caster.get_value_direct(10), 11)
    self.assertEqual(type_caster.get_value_optional(12), 13)
    self.assertEqual(type_caster.get_value_variant(14), 15)
    self.assertEqual(type_caster.return_value(11), 12)
    self.assertCountEqual(
        type_caster.return_value_list([11, 12, 13]), [12, 13, 14])
    self.assertEqual(type_caster.consume_unique_ptr(10), 11)

  def test_pyobjfrom_only(self):
    self.assertEqual(type_caster.return_value_pyobjfrom_only(11), 13)

  def test_pyobjas_only(self):
    self.assertEqual(type_caster.get_value_pyobjas_only(10), 13)

  @absltest.skipIf(
      'pybind11' not in type_caster.__doc__,
      'Legacy PyCLIF does not recognize `Pybind11Ignore` in '
      '`CLIF use` comments')
  def test_pybind11_ignore(self):
    with self.assertRaises(TypeError):
      type_caster.get_value_pybind11_ignore(10)

  def test_template(self):
    self.assertEqual(type_caster.get_value_template_one_param(10), 14)
    self.assertEqual(type_caster.get_value_template_two_params(10), 15)

  @parameterized.parameters(
      type_caster.get_refcount_from_raw_ptr,
      type_caster.get_refcount_from_unique_ptr,
      type_caster.get_refcount_from_rvalue,
      type_caster.get_refcount_from_const_ref,
      type_caster.get_refcount_from_const_ptr,
      type_caster.get_refcount_from_enum)
  def test_generated_pyobjfrom(self, func):
    res = func()
    self.assertGreater(res, 0)

  def test_convert_python_object_to_cpp(self):
    e = lambda_expressions.SomeEnum.first
    self.assertTrue(type_caster.can_convert_enum_to_concrete(e))
    self.assertFalse(type_caster.can_convert_enum_to_concrete('10'))
    arg = lambda_expressions.Arg()
    self.assertTrue(type_caster.can_convert_to_concrete(arg))
    self.assertFalse(type_caster.can_convert_to_concrete('10'))
    self.assertTrue(type_caster.can_convert_to_ptr(arg))
    self.assertFalse(type_caster.can_convert_to_ptr(10))
    self.assertTrue(type_caster.can_convert_to_shared_ptr(arg))
    self.assertFalse(type_caster.can_convert_to_shared_ptr(['10']))
    self.assertTrue(type_caster.can_convert_to_unique_ptr(arg))
    self.assertFalse(type_caster.can_convert_to_unique_ptr({10: '10'}))

  def test_pyobject_type_caster(self):
    inp_list = [PyValueHolder(1), PyValueHolder(2), PyValueHolder(3)]
    # Without the for loop ASAN did not reliably detect heap-use-after-free
    # when Py_INCREF(e) was missing in the pyobject_round_trip() C++ function.
    for _ in range(1000):
      out_list = type_caster.pyobject_round_trip(inp_list)
      for inp, out in zip(inp_list, out_list):
        self.assertIs(inp, out)

  def test_abstract_type_type_caster(self):
    self.assertEqual(type_caster.abstract_raw_ptr_round_trip(10), 12)
    self.assertEqual(type_caster.abstract_shared_ptr_round_trip(10), 11)
    self.assertEqual(type_caster.abstract_unique_ptr_round_trip(10), 12)
    self.assertEqual(type_caster.return_abstract_no_pyobjas(10), 10)

  def test_only_optional_conversion_type_caster(self):
    self.assertEqual(type_caster.consume_only_optional_conversion(10), 20)

  def test_only_ptr_to_ptr_conversion_type_caster(self):
    self.assertEqual(type_caster.consume_only_ptr_to_ptr_conversion(10), 110)

  def test_only_shared_ptr_conversion_type_caster(self):
    self.assertEqual(type_caster.consume_only_shared_ptr_conversion(10), 10)

  def test_multiple_conversions_type_caster(self):
    self.assertEqual(type_caster.consume_multiple_conversions(10), 1010)

  def test_ptr_in_clif_use_comment(self):
    self.assertEqual(type_caster.consume_ptr_in_clif_use_comment(10), 10010)

  def test_function_throw_python_exception(self):
    self.assertEqual(type_caster.return_pyobject_throw_python_exception(10), 10)
    with self.assertRaisesRegex(ValueError, r'Value < 0'):
      type_caster.return_pyobject_throw_python_exception(-1)


if __name__ == '__main__':
  absltest.main()
