# Copyright 2020 Google Inc.
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

"""Tests for clif.testing.python.nonzero_mapping."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import nonzero_mapping
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import nonzero_mapping_pybind11
except ImportError:
  nonzero_mapping_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (nonzero_mapping,
                                             nonzero_mapping_pybind11))
    if np[1] is not None
])
class NonzeroMappingTest(absltest.TestCase):

  def testDefaultCppName(self, wrapper_lib):
    always_false = wrapper_lib.AlwaysFalse()
    self.assertEqual(bool(always_false), False)

  def testCustomizedCppName(self, wrapper_lib):
    might_be_true = wrapper_lib.MightBeTrue(False)
    self.assertEqual(bool(might_be_true), False)
    might_be_true = wrapper_lib.MightBeTrue(True)
    self.assertEqual(bool(might_be_true), True)


if __name__ == '__main__':
  absltest.main()
