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

"""Tests for clif.testing.python.t6."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import t6
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import t6_pybind11
except ImportError:
  t6_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (t6, t6_pybind11))
    if np[1] is not None
])
class T6Test(absltest.TestCase):

  def testListInt(self, wrapper_lib):
    self.assertEqual(wrapper_lib.Repeat([1, 2], 3), [1, 2, 1, 2, 1, 2])


if __name__ == '__main__':
  absltest.main()
