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

from clif.testing.python import python_multiple_inheritance as tm


class PC(tm.CppBase):
  pass


class PPCC(PC, tm.CppDrvd):
  pass


class PPCCInit(PC, tm.CppDrvd):

  def __init__(self, value):
    PC.__init__(self, value)
    tm.CppDrvd.__init__(self, value + 1)


class PythonMultipleInheritanceTest(absltest.TestCase):

  def testPC(self):
    d = PC(11)
    self.assertEqual(d.get_base_value(), 11)
    d.reset_base_value(13)
    self.assertEqual(d.get_base_value(), 13)

  @absltest.skipIf(
      "pybind11" in tm.__doc__,
      "Preempt `__init__() must be called when overriding __init__` exception.",
  )
  def testPPCC(self):
    d = PPCC(11)
    self.assertEqual(d.get_drvd_value(), 33)
    d.reset_drvd_value(55)
    self.assertEqual(d.get_drvd_value(), 55)

    # PyCLIF-C-API: CppBase is not initialized and never used.
    self.assertEqual(d.get_base_value(), 11)
    self.assertEqual(d.get_base_value_from_drvd(), 11)
    d.reset_base_value(20)
    self.assertEqual(d.get_base_value(), 20)
    self.assertEqual(d.get_base_value_from_drvd(), 20)
    d.reset_base_value_from_drvd(30)
    self.assertEqual(d.get_base_value(), 30)
    self.assertEqual(d.get_base_value_from_drvd(), 30)

  def testPPCCInit(self):
    d = PPCCInit(11)
    self.assertEqual(d.get_drvd_value(), 36)
    d.reset_drvd_value(55)
    self.assertEqual(d.get_drvd_value(), 55)

    # PyCLIF-C-API: CppBase is initialized but never used.
    # PyCLIF-pybind11: CppBase is initialized and used when CppBase methods
    #                  are called, but CppDrvd is used when CppDrvd methods
    #                  are called.
    i = 1 if "pybind11" in tm.__doc__ else 0
    self.assertEqual(d.get_base_value(), (12, 11)[i])
    self.assertEqual(d.get_base_value_from_drvd(), 12)
    d.reset_base_value(20)
    self.assertEqual(d.get_base_value(), 20)
    self.assertEqual(d.get_base_value_from_drvd(), (20, 12)[i])
    d.reset_base_value_from_drvd(30)
    self.assertEqual(d.get_base_value(), (30, 20)[i])
    self.assertEqual(d.get_base_value_from_drvd(), 30)


if __name__ == "__main__":
  absltest.main()
