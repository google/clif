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

"""Tests for clif.testing.python.nested_types."""

from absl.testing import absltest

from clif.testing.python import nested_types


class NestedTypesTest(absltest.TestCase):

  def testModuleAttr(self):
    expected_module_name = nested_types.__name__
    for ty in (nested_types.Outer1,
               nested_types.Outer1.Inner,
               nested_types.Outer2,
               nested_types.Outer2.Inner,
               nested_types.Outer3,
               nested_types.Outer3.Inner,
               nested_types.Outer4,
               nested_types.Outer4.Inner,
               nested_types.Outer,
               nested_types.Outer.Inner,):
      self.assertEqual(ty.__module__, expected_module_name)

  def testNestedTypes(self):
    inner1 = nested_types.Outer1.Inner()
    inner1.a = 100
    self.assertEqual(inner1.a, 100)

    inner2 = nested_types.Outer2.Inner()
    inner2.b = 100
    self.assertEqual(inner2.b, 100)

    k1 = nested_types.Outer3.Inner.k1
    self.assertEqual(k1.value, 123)
    k2 = nested_types.Outer3.Inner.k2
    self.assertEqual(k2.value, 234)

    k1 = nested_types.Outer4.Inner.k1
    self.assertEqual(k1.value, 321)
    k2 = nested_types.Outer4.Inner.k2
    self.assertEqual(k2.value, 432)

    k1 = nested_types.Outer.Inner.k1
    self.assertEqual(k1.value, 234)
    k2 = nested_types.Outer.Inner.k2
    self.assertEqual(k2.value, 567)


if __name__ == '__main__':
  absltest.main()
