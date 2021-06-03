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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import postproc
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import postproc_pybind11
except ImportError:
  postproc_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (postproc, postproc_pybind11))
    if np[1] is not None
])
class PostProctest(absltest.TestCase):

  def testAsSortedList(self, wrapper_lib):
    ret = wrapper_lib.as_sorted_list(0)
    self.assertListEqual(ret, [])
    ret = wrapper_lib.as_sorted_list(1)
    self.assertListEqual(ret, ['5'])
    ret = wrapper_lib.as_sorted_list(3)
    self.assertListEqual(ret, ['11', '5', '8'])  # Sorted lexically.

  def testAsSortedTuple(self, wrapper_lib):
    ret = wrapper_lib.as_sorted_tuple(0)
    self.assertSequenceEqual(ret, ())
    ret = wrapper_lib.as_sorted_tuple(1)
    self.assertSequenceEqual(ret, ('5'))
    ret = wrapper_lib.as_sorted_tuple(3)
    self.assertSequenceEqual(ret, ('11', '5', '8'))  # Sorted lexically.

  def testInvalidPostproc(self, wrapper_lib):
    with self.assertRaises(TypeError):
      wrapper_lib.invalid_postproc(0)

  def testValueErrorOnFalse(self, wrapper_lib):
    ret = wrapper_lib.value_error_on_false(input=1)
    self.assertEqual(ret, 2)
    with self.assertRaises(ValueError):
      wrapper_lib.value_error_on_false(input=-1)

  def testRuntimeErrorOnFalse(self, wrapper_lib):
    ret = wrapper_lib.runtime_error_on_false(input=1)
    self.assertEqual(ret, 2)
    with self.assertRaises(RuntimeError):
      wrapper_lib.runtime_error_on_false(input=-1)

  def testIgnoreTrueOrFalse(self, wrapper_lib):
    ret = wrapper_lib.ignore_true_or_false(input=1)
    self.assertEqual(ret, 2)
    ret = wrapper_lib.ignore_true_or_false(input=-1)
    self.assertEqual(ret, -1)

  def testGetOne(self, wrapper_lib):
    ret = wrapper_lib.get_one()
    self.assertIsInstance(ret, str)
    self.assertEqual(ret, '\x01')


if __name__ == '__main__':
  absltest.main()
