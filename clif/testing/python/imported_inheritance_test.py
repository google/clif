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
from absl.testing import parameterized

from clif.testing.python import imported_inheritance
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import imported_inheritance_pybind11
except ImportError:
  imported_inheritance_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (imported_inheritance,
                                             imported_inheritance_pybind11))
    if np[1] is not None
])
class ImportedInheritanceTest(absltest.TestCase):

  def testInheritNestedInner(self, wrapper_lib):
    n = wrapper_lib.InheritImportedNestedInner()
    n.a = 100
    self.assertEqual(n.a, 100)

  def testInheritNested(self, wrapper_lib):
    n = wrapper_lib.InheritImportedNested()
    n.a = 100
    self.assertEqual(n.a, 100)


if __name__ == '__main__':
  absltest.main()
