# Copyright 2017 Google Inc.
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

"""Tests for clif.testing.python.slots."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import slots
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import slots_pybind11
except ImportError:
  slots_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (slots, slots_pybind11))
    if np[1] is not None
])
class SlotsTest(absltest.TestCase):

  def testObjectMethods(self, wrapper_lib):
    a = wrapper_lib.I5()
    self.assertEqual(hash(a), 0)

  def testRO(self, wrapper_lib):
    if wrapper_lib is slots_pybind11:  # b/184390527
      self.skipTest('pybind11 generates a segfault when calling list(a)')
    a = wrapper_lib.I5()
    self.assertLen(a, 5)
    self.assertEqual(list(a), [0]*5)
    a[1] = 1
    self.assertEqual(a[1], 1)
    self.assertEqual(list(a), [0, 1, 0, 0, 0])
    with self.assertRaises(NotImplementedError):
      del a[1]

  def testRW(self, wrapper_lib):
    if wrapper_lib is slots_pybind11:  # b/184390527
      self.skipTest('pybind11 generates a segfault when calling list(a)')
    a = wrapper_lib.Z5()
    self.assertLen(a, 5)
    self.assertEqual(list(a), [0]*5)
    a[1] = 1
    self.assertEqual(a[1], 1)
    self.assertEqual(list(a), [0, 1, 0, 0, 0])
    del a[1]
    self.assertEqual(list(a), [0]*5)

  def testHashSmallInt(self, wrapper_lib):
    a = wrapper_lib.I5()
    a[2] = 3
    a[4] = 5
    self.assertEqual(hash(a), 8)

  def testHashSsizetOverflow(self, wrapper_lib):
    a = wrapper_lib.I5()
    a[0] = 999
    self.assertNotEqual(hash(a), 999)

  def testUnHashable(self, wrapper_lib):
    a = wrapper_lib.Z5()
    with self.assertRaises(TypeError) as ctx:
      hash(a)
    self.assertIn(' int', str(ctx.exception))


if __name__ == '__main__':
  absltest.main()
