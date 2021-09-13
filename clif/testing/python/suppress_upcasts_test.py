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

"""Tests for clif.testing.python.suppress_upcasts."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import suppress_upcasts
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import suppress_upcasts_pybind11
except ImportError:
  suppress_upcasts_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (suppress_upcasts,
                                             suppress_upcasts_pybind11))
    if np[1] is not None
])
class SpupressUpcastsTest(absltest.TestCase):

  def testClassWithoutUpcasts(self, wrapper_lib):
    obj = wrapper_lib.DerivedSuppressUpcasts()
    self.assertEqual(obj.value(), 20)


if __name__ == '__main__':
  absltest.main()
