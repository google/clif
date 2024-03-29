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

from clif.testing.python import copy_move_types_custom_from_as as tm
from clif.testing.python import copy_move_types_library

ENV_IX = 1
if tm.__pyclif_codegen_mode__ == "pybind11":
  ENV_IX += 2


class CopyMoveTypesCustomFromAsTestCase(absltest.TestCase):

  def testFromCRAsPCopyMoveType(self):
    # Default clif type caster
    class_obj = copy_move_types_library.CopyMoveType()
    cfa_obj = tm.MakeFromCRAsPCopyMoveType(class_obj)
    trace = tm.GetTraceFromCRAsPCopyMoveType(cfa_obj)
    self.assertEqual(
        trace,
        [
            "DefaultCtor_CpCtor_CpCtor_CpLhs",
            "DefaultCtor_CpCtor_MvLhs_CpCtor_CpLhs",
            "DefaultCtor_CpCtor_CpCtor_CpLhs_MvCtorTo",
        ][ENV_IX],
    )

  def testFromCRAsSOCopyMoveType(self):
    # std::optional
    class_obj = copy_move_types_library.CopyMoveType()
    cfa_obj = tm.MakeFromCRAsOpCopyMoveType(class_obj)
    trace = tm.GetTraceFromCRAsOpCopyMoveType(cfa_obj)
    self.assertEqual(
        trace,
        [
            "DefaultCtor_CpCtor_CpCtor_CpLhs_CpCtor_MvCtorTo",
            "DefaultCtor_CpCtor_MvLhs_CpCtor_CpLhs_CpCtor_MvCtorTo",
            "DefaultCtor_CpCtor_CpCtor_CpLhs_CpCtor_MvCtorTo_MvCtorTo_MvCtorTo",
        ][ENV_IX],
    )

  def testFromCRAsPPCopyMoveType(self):
    # Pointer to pointer
    class_obj = copy_move_types_library.CopyMoveType()
    cfa_obj = tm.MakeFromCRAsPPCopyMoveType(class_obj)
    trace = tm.GetTraceFromCRAsPPCopyMoveType(cfa_obj)
    self.assertEqual(
        trace,
        [
            "DefaultCtor_CpCtor_CpCtor",
            "DefaultCtor_CpCtor_MvCtorTo_CpCtor",
            "DefaultCtor_CpCtor_CpCtor",
        ][ENV_IX],
    )

  def testFromCRAsUPCopyMoveType(self):
    # std::unique_ptr
    class_obj = copy_move_types_library.CopyMoveType()
    cfa_obj = tm.MakeFromCRAsUpCopyMoveType(class_obj)
    trace = tm.GetTraceFromCRAsUpCopyMoveType(cfa_obj)
    self.assertEqual(
        trace,
        [
            "DefaultCtor_CpCtor_CpCtor_CpLhs_CpCtor",
            "DefaultCtor_CpCtor_MvLhs_CpCtor_CpLhs_CpCtor",
            "DefaultCtor_CpCtor_CpCtor_CpLhs_CpCtor",
        ][ENV_IX],
    )

  def testFromCRAsSPCopyMoveType(self):
    # std::shared_ptr
    class_obj = copy_move_types_library.CopyMoveType()
    cfa_obj = tm.MakeFromCRAsSpCopyMoveType(class_obj)
    trace = tm.GetTraceFromCRAsSpCopyMoveType(cfa_obj)
    self.assertEqual(
        trace,
        [
            "DefaultCtor_CpCtor_CpCtor_CpLhs",
            "DefaultCtor_CpCtor_MvLhs_CpCtor_CpLhs",
            "DefaultCtor_CpCtor_CpCtor_CpLhs_CpCtor_MvCtorTo",
        ][ENV_IX],
    )


if __name__ == "__main__":
  absltest.main()
