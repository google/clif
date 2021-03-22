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

"""Tests for clif.testing.python.t10."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import t10
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import t10_pybind11
except ImportError:
  t10_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (t10, t10_pybind11))
    if np[1] is not None
])
class T10Test(absltest.TestCase):

  def testImportedClass(self, wrapper_lib):
    k = wrapper_lib.CreateK()
    self.assertTrue(k.Int1)

  def testDerivedClass(self, wrapper_lib):
    a = wrapper_lib.A()
    self.assertEqual(wrapper_lib.A.C, 1)
    self.assertEqual(a.C, 1)
    self.assertEqual(str(a), 'A')

if __name__ == '__main__':
  absltest.main()
