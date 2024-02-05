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

from clif.testing.python import python_multiple_inheritance as tm


class PC(tm.CppBase):
  pass


class PPCC(PC, tm.CppDrvd):
  pass


class PCExplicitInitWithSuper(tm.CppBase):

  def __init__(self, value):
    super().__init__(value + 1)


class PCExplicitInitMissingSuper(tm.CppBase):

  def __init__(self, value):
    del value


class PCExplicitInitMissingSuper2(tm.CppBase):

  def __init__(self, value):
    del value


class PythonMultipleInheritanceTest(parameterized.TestCase):

  def testPC(self):
    d = PC(11)
    self.assertEqual(d.get_base_value(), 11)
    d.reset_base_value(13)
    self.assertEqual(d.get_base_value(), 13)

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

  def testPCExplicitInitWithSuper(self):
    d = PCExplicitInitWithSuper(14)
    self.assertEqual(d.get_base_value(), 15)

  @parameterized.parameters(
      PCExplicitInitMissingSuper, PCExplicitInitMissingSuper2
  )
  def testPCExplicitInitMissingSuper(self, derived_type):
    with self.assertRaises(TypeError) as ctx:
      derived_type(0)
    self.assertEndsWith(
        str(ctx.exception),
        "python_multiple_inheritance.CppBase.__init__() must be called when"
        " overriding __init__",
    )

  def testDerivedTpInitRegistryWeakrefBasedCleanup(self):
    def NestedFunction(i):
      class NestedClass(tm.CppBase):

        def __init__(self, value):
          super().__init__(value + 3)

      d1 = NestedClass(i + 7)
      d2 = NestedClass(i + 8)
      return (d1.get_base_value(), d2.get_base_value())

    for _ in range(100):
      self.assertEqual(NestedFunction(0), (10, 11))
      self.assertEqual(NestedFunction(3), (13, 14))


if __name__ == "__main__":
  absltest.main()
