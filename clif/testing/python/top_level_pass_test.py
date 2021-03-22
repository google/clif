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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import top_level_pass
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import top_level_pass_pybind11
except ImportError:
  top_level_pass_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (top_level_pass,
                                             top_level_pass_pybind11))
    if np[1] is not None
])
class TopLevelPassTest(absltest.TestCase):

  def testEmptyModule(self, wrapper_lib):
    self.assertRegexpMatches(  # pylint: disable=deprecated-method
        wrapper_lib.__doc__, 'CLIF-generated module for .*top_level_pass.clif')


if __name__ == '__main__':
  absltest.main()
