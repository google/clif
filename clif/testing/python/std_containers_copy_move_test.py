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

from clif.testing.python import copy_move_types_custom_from_as
from clif.testing.python import copy_move_types_library
from clif.testing.python import std_containers_copy_move as tm

GEN_IX = 1 if "pybind11" in tm.__doc__ else 0


class StdContainersCopyMoveTestCase(parameterized.TestCase):

  @parameterized.parameters([
      (
          "StdVector",
          ["DefaultCtor_CpLhs_MvCtorTo@", "DefaultCtor_CpCtor@"][GEN_IX],
      ),
      (
          "StdArray1",
          ["DefaultCtor_CpLhs_MvLhs@", "DefaultCtor_CpLhs_MvCtorTo@"][GEN_IX],
      ),
  ])
  def testPassSeqCopyMoveType(self, std_type_name, expected_traces):
    obj = copy_move_types_library.CopyMoveType()
    traces = getattr(tm, f"Pass{std_type_name}CopyMoveType")([obj])
    self.assertEqual(obj.trace, "DefaultCtor")
    self.assertEqual(traces, expected_traces)

  @parameterized.parameters(["StdVector", "StdArray1"])
  def testPassSeqStayPutTypePtr(self, std_type_name):
    obj = copy_move_types_library.StayPutType()
    traces = getattr(tm, f"Pass{std_type_name}StayPutTypePtr")([obj])
    self.assertEqual(obj.trace, "DefaultCtor")
    self.assertEqual(traces, "DefaultCtor@")

  def testPassStdVectorFromCRAsPPCopyMoveType(self):
    class_obj = copy_move_types_library.CopyMoveType()
    cfa_obj = copy_move_types_custom_from_as.MakeFromCRAsPPCopyMoveType(
        class_obj
    )
    self.assertEqual(
        copy_move_types_custom_from_as.GetTraceFromCRAsPPCopyMoveType(cfa_obj),
        "DefaultCtor_CpCtor_CpCtor",
    )
    traces = tm.PassStdVectorFromCRAsPPCopyMoveType([cfa_obj])
    self.assertEqual(
        copy_move_types_custom_from_as.GetTraceFromCRAsPPCopyMoveType(cfa_obj),
        [
            "DefaultCtor_CpCtor_CpCtor",
            "DefaultCtor_CpCtor_CpCtor_MvCtorFrom",  # b/287289622#comment32
        ][GEN_IX],
    )
    self.assertEqual(
        traces,
        [
            "DefaultCtor_CpCtor_CpCtor_CpCtor_MvCtorTo@",
            "DefaultCtor_CpCtor_CpCtor_MvCtorTo@",
        ][GEN_IX],
    )


if __name__ == "__main__":
  absltest.main()
