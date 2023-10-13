# Copyright 2023 Google LLC
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
from absl.testing import parameterized

from clif.testing.python import copy_move_types_library as tm

LIBRARY_TYPE_NAMES = (
    "CopyMoveType",
    "CopyOnlyType",
    "MoveOnlyType",
    "StayPutType",
)


class CopyMoveTypesLibraryTestCase(parameterized.TestCase):

  @parameterized.parameters(*LIBRARY_TYPE_NAMES)
  def testDefaultCtor(self, type_name):
    obj = getattr(tm, type_name)()
    self.assertEqual(obj.trace, "DefaultCtor")

  @parameterized.parameters(*LIBRARY_TYPE_NAMES)
  def testCtorArg(self, type_name):
    obj = getattr(tm, type_name)("CtorArg")
    self.assertEqual(obj.trace, "CtorArg")


if __name__ == "__main__":
  absltest.main()
