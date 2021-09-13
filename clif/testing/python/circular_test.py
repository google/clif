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

"""Tests for clif.testing.python.circular."""

from absl.testing import absltest

# pylint: disable=unused-import
from clif.testing.python import circular


class CircularTest(absltest.TestCase):

  def testEverythingBuilt(self):
    # Nothing to test: if we can import circular, then that means
    # we were able to compile the clif file to cpp code.
    pass


if __name__ == '__main__':
  absltest.main()
