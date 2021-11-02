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
"""Tests for clif.testing.python.nested_inheritance_external."""

from absl.testing import absltest

from clif.testing.python import imported_inheritance


class ImportedInheritanceTest(absltest.TestCase):

  def testInheritNestedInner(self):
    n = imported_inheritance.InheritImportedNestedInner()
    n.a = 100
    self.assertEqual(n.a, 100)

  def testInheritNested(self):
    n = imported_inheritance.InheritImportedNested()
    n.a = 100
    self.assertEqual(n.a, 100)

  def testInheritFields(self):
    n = imported_inheritance.InheritImportedNestedField()
    n.i = 100
    self.assertEqual(n.i, 100)


if __name__ == '__main__':
  absltest.main()
