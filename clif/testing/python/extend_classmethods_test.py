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

from clif.testing.python import extend_classmethods


class ExtendClassmethodsTest(absltest.TestCase):

  def setUp(self):
    super().setUp()
    extend_classmethods.Abc.set_static_value(5432)

  def test_create_from_value(self):
    expected_value = 543
    abc = extend_classmethods.Abc.from_value(expected_value)
    self.assertEqual(abc.get_value(), expected_value)

  def test_set_class_variable(self):
    self.assertEqual(extend_classmethods.Abc.get_static_value(), 5432)

  def test_function_with_defaults(self):
    fwd = extend_classmethods.Abc.function_with_defaults
    self.assertEqual(fwd(), (5432 * 3 + 5) * 7)
    self.assertEqual(fwd(2), (5432 * 2 + 5) * 7)
    self.assertEqual(fwd(2, 6), (5432 * 2 + 6) * 7)
    self.assertEqual(fwd(2, 6, 8), (5432 * 2 + 6) * 8)
    self.assertEqual(fwd(i=11), (5432 * 11 + 5) * 7)
    self.assertEqual(fwd(j=13), (5432 * 3 + 13) * 7)
    self.assertEqual(fwd(k=15), (5432 * 3 + 5) * 15)

  def test_nested_classmethod(self):
    v = extend_classmethods.TestNestedClassmethod.Inner.get_static_value()
    self.assertEqual(v, 472)


if __name__ == '__main__':
  absltest.main()
