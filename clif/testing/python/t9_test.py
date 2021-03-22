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

"""Tests for clif.testing.python.t9."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import t9
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import t9_pybind11
except ImportError:
  t9_pybind11 = None
# pylint: enable=g-import-not-at-top


class PyCore(t9.Core):
  pass


class PyDerived(t9.Derived):
  pass


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (t9, t9_pybind11))
    if np[1] is not None
])
class T9Test(absltest.TestCase):

  def testCapsule(self, wrapper_lib):
    d = wrapper_lib.Derived()
    self.assertEqual(d.Value(), 2)
    self.assertTrue(wrapper_lib.IsDerived(d))

  def testCore(self, wrapper_lib):
    self.assertEqual(wrapper_lib.CoreValue(wrapper_lib.Core()), 12)
    self.assertEqual(wrapper_lib.CoreValue(wrapper_lib.Derived()), 12)
    self.assertEqual(wrapper_lib.CoreValue(PyCore()), 12)
    self.assertEqual(wrapper_lib.CoreValue(PyDerived()), 12)

  def testVirtualDerived(self, wrapper_lib):
    self.assertEqual(wrapper_lib.Derived().CoreValue(), 12)
    self.assertEqual(PyDerived().CoreValue(), 12)
    self.assertTrue(wrapper_lib.Core.IsDestructed(), '~Core() not called')

  def testPyFromCapsule(self, wrapper_lib):
    self.assertIsNotNone(wrapper_lib.NewAbstract())


if __name__ == '__main__':
  absltest.main()
