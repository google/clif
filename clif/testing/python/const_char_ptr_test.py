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

from clif.testing.python import const_char_ptr


class ConstCharPtrTest(absltest.TestCase):

  def testReturnConstCharPtrAsStr(self):
    res = const_char_ptr.ReturnConstCharPtrAsStr()
    self.assertIsInstance(res, str)
    self.assertEqual(res, 'string literal')

  def testReturnConstCharPtrAsBytes(self):
    res = const_char_ptr.ReturnConstCharPtrAsBytes()
    if 'pybind11' not in const_char_ptr.__doc__:
      # BUG: Return value should be bytes but is str (Python 3).
      self.assertIsInstance(res, str)  # Should be bytes.
      self.assertEqual(res, 'string literal')  # Should be b'string literal'.
    else:
      self.assertIsInstance(res, bytes)
      self.assertEqual(res, b'string literal')


if __name__ == '__main__':
  absltest.main()
