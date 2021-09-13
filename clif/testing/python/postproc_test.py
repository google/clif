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

from clif.testing.python import postproc


class PostProctest(absltest.TestCase):

  def testAsSortedList(self):
    ret = postproc.as_sorted_list(0)
    self.assertListEqual(ret, [])
    ret = postproc.as_sorted_list(1)
    self.assertListEqual(ret, ['5'])
    ret = postproc.as_sorted_list(3)
    self.assertListEqual(ret, ['11', '5', '8'])  # Sorted lexically.

  def testAsSortedTuple(self):
    ret = postproc.as_sorted_tuple(0)
    self.assertSequenceEqual(ret, ())
    ret = postproc.as_sorted_tuple(1)
    self.assertSequenceEqual(ret, ('5'))
    ret = postproc.as_sorted_tuple(3)
    self.assertSequenceEqual(ret, ('11', '5', '8'))  # Sorted lexically.

  def testInvalidPostproc(self):
    with self.assertRaises(TypeError):
      postproc.invalid_postproc(0)

  def testValueErrorOnFalse(self):
    ret = postproc.value_error_on_false(input=1)
    self.assertEqual(ret, 2)
    with self.assertRaises(ValueError):
      postproc.value_error_on_false(input=-1)

  def testRuntimeErrorOnFalse(self):
    ret = postproc.runtime_error_on_false(input=1)
    self.assertEqual(ret, 2)
    with self.assertRaises(RuntimeError):
      postproc.runtime_error_on_false(input=-1)

  def testIgnoreTrueOrFalse(self):
    ret = postproc.ignore_true_or_false(input=1)
    self.assertEqual(ret, 2)
    ret = postproc.ignore_true_or_false(input=-1)
    self.assertEqual(ret, -1)

  def testGetOne(self):
    ret = postproc.get_one()
    self.assertIsInstance(ret, str)
    self.assertEqual(ret, '\x01')


if __name__ == '__main__':
  absltest.main()
