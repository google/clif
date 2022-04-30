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

from clif.testing.python import t9


class PyCore(t9.Core):
  pass


class PyDerived(t9.Derived):
  pass


class T9Test(absltest.TestCase):

  def testCapsule(self):
    d = t9.Derived()
    self.assertEqual(d.Value(), 2)
    self.assertTrue(t9.IsDerived(d))
    self.assertTrue(t9.IsDerivedConstRef(d))

  def testCore(self):
    self.assertEqual(t9.CoreValue(t9.Core()), 12)
    self.assertEqual(t9.CoreValue(t9.Derived()), 12)
    self.assertEqual(t9.CoreValue(PyCore()), 12)
    self.assertEqual(t9.CoreValue(PyDerived()), 12)

  def testVirtualDerived(self):
    self.assertEqual(t9.Derived().CoreValue(), 12)
    self.assertEqual(PyDerived().CoreValue(), 12)
    self.assertTrue(t9.Core.IsDestructed(), '~Core() not called')

  def testPyFromCapsule(self):
    self.assertIsNotNone(t9.NewAbstract())


if __name__ == '__main__':
  absltest.main()
