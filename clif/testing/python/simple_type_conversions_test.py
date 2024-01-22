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

from clif.testing.python import simple_type_conversions as tm


class SimpleTypeConversions(absltest.TestCase):

  def testSignedCharManipulation(self):
    self.assertEqual(tm.SignedCharManipulation(2), 29)
    for inp in [-129, 128]:
      if tm.__pyclif_codegen_mode__ == 'pybind11':
        with self.assertRaises(TypeError) as ctx:
          tm.SignedCharManipulation(inp)
        self.assertIn('incompatible function arguments.', str(ctx.exception))
      else:
        with self.assertRaises(TypeError) as ctx:
          tm.SignedCharManipulation(inp)
        self.assertEqual(
            str(ctx.exception),
            'SignedCharManipulation() argument inp is not valid for'
            ' signed char (int instance given):'
            ' value %d is out of range for signed char' % inp)

  def testUnsignedCharManipulation(self):
    self.assertEqual(tm.UnsignedCharManipulation(3), 39)
    if tm.__pyclif_codegen_mode__ == 'pybind11':
      with self.assertRaises(TypeError) as ctx:
        tm.SignedCharManipulation(256)
      self.assertIn('incompatible function arguments.', str(ctx.exception))
    else:
      with self.assertRaises(TypeError) as ctx:
        tm.UnsignedCharManipulation(256)
      self.assertEqual(
          str(ctx.exception),
          'UnsignedCharManipulation() argument inp is not valid for'
          ' unsigned char (int instance given):'
          ' value 256 is too large for unsigned char')

  def testPassUint32InRange(self):
    self.assertEqual(tm.PassUint32(0), '0')
    self.assertEqual(tm.PassUint32(2**32 - 1), '4294967295')

  def testPassUint32Negative(self):
    if tm.__pyclif_codegen_mode__ == 'pybind11':
      with self.assertRaisesRegex(
          TypeError, r'PassUint32\(\): incompatible function arguments.*'
      ):
        tm.PassUint32(-1)
    else:
      with self.assertRaisesRegex(
          TypeError,
          r'PassUint32\(\) argument val is not valid for unsigned int \(int'
          r" instance given\): can't convert negative value to unsigned int",
      ):
        tm.PassUint32(-1)

  def testPassUint32OutOfRange(self):
    if tm.__pyclif_codegen_mode__ == 'pybind11':
      with self.assertRaisesRegex(
          TypeError, r'PassUint32\(\): incompatible function arguments.*'
      ):
        tm.PassUint32(2**32)
    else:
      with self.assertRaisesRegex(
          TypeError,
          r'PassUint32\(\) argument val is not valid for unsigned int \(int'
          r' instance given\): value too large for unsigned int',
      ):
        tm.PassUint32(2**32)

  def testPassInt64(self):
    i64max = 2**63 - 1
    i64max_str = '9223372036854775807'
    self.assertEqual(tm.PassInt64ByValueInt(i64max), i64max_str)
    self.assertEqual(tm.PassInt64ByValueInt64AsInt(i64max), i64max_str)
    self.assertEqual(tm.PassInt64ConstRefInt64AsInt(i64max), i64max_str)
    if tm.__pyclif_codegen_mode__ == 'pybind11':
      # Partial error message (to not exercise pybind11 details).
      expected = r'\(val: int\) -> object'
    else:
      # Full error message (exercising PyCLIF details).
      expected = (
          r'^PassInt64ConstRefInt\(\) argument val is not valid for int \(int'
          r' instance given\): value too large for int$'
      )
    with self.assertRaisesRegex(TypeError, expected):
      # THIS BEHAVIOR IS UNDESIRABLE. Ideally the matcher would be changed to
      # handle this situation more consistently with the other three cases
      # above.
      # To make this more concrete, the PyCLIF-C-API generated code is:
      #     int arg1;
      #     if (!Clif_PyObjAs(a[0], &arg1)) return ArgError(...);
      # for this case, while it is
      #     long arg1;
      # for the other three cases above. The difference is that the matcher
      # does not update `func.params.type.cpp_type` correctly for the
      # `const std::int64_t&` case.
      # NOTE, just in case: On a platform where C++ `int` is 64 bits, this
      #                     will not raise an exception. Please generalize
      #                     this test as needed.
      tm.PassInt64ConstRefInt(i64max)


if __name__ == '__main__':
  absltest.main()
