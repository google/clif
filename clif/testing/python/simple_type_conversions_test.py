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
      if 'pybind11' in tm.__doc__:
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
    if 'pybind11' in tm.__doc__:
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
    if 'pybind11' in tm.__doc__:
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
    if 'pybind11' in tm.__doc__:
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


if __name__ == '__main__':
  absltest.main()
