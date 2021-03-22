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
from absl.testing import parameterized

from clif.testing.python import nested_types
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import nested_types_pybind11
except ImportError:
  nested_types_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np
    for np in zip(('c_api', 'pybind11'), (nested_types, nested_types_pybind11))
    if np[1] is not None
])
class NestedTypesTest(absltest.TestCase):

  def testModuleAttr(self, wrapper_lib):
    expected_module_name = wrapper_lib.__name__
    for ty in (wrapper_lib.Outer1,
               wrapper_lib.Outer1.Inner,
               wrapper_lib.Outer2,
               wrapper_lib.Outer2.Inner,
               wrapper_lib.Outer3,
               wrapper_lib.Outer3.Inner,
               wrapper_lib.Outer4,
               wrapper_lib.Outer4.Inner,
               wrapper_lib.Outer,
               wrapper_lib.Outer.Inner,):
      self.assertEqual(ty.__module__, expected_module_name)

  def testNestedTypes(self, wrapper_lib):
    inner1 = wrapper_lib.Outer1.Inner()
    inner1.a = 100
    self.assertEqual(inner1.a, 100)

    inner2 = wrapper_lib.Outer2.Inner()
    inner2.b = 100
    self.assertEqual(inner2.b, 100)

    k1 = wrapper_lib.Outer3.Inner.k1
    self.assertEqual(k1.value, 123)
    k2 = wrapper_lib.Outer3.Inner.k2
    self.assertEqual(k2.value, 234)

    k1 = wrapper_lib.Outer4.Inner.k1
    self.assertEqual(k1.value, 321)
    k2 = wrapper_lib.Outer4.Inner.k2
    self.assertEqual(k2.value, 432)

    k1 = wrapper_lib.Outer.Inner.k1
    self.assertEqual(k1.value, 234)
    k2 = wrapper_lib.Outer.Inner.k2
    self.assertEqual(k2.value, 567)


if __name__ == '__main__':
  absltest.main()
