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

from unittest import mock

from absl.testing import absltest

from clif.testing.python import mock_uninitializable as tm

# tm.NoCtor is this PyCLIF-wrapped C++ type:
#
#     struct NoCtor {
#       NoCtor() = delete;
#       int Mul100(int i) const { return i * 100; }
#     };
#
# It cannot be initialized from Python. NoCtor here is contrived, but there are
# sound design choices leading to this situation.


class PseudoModule:  # To make this similar to the extension situation.

  class NativeNoCtor:

    def __init__(self):
      raise RuntimeError("Meant to be inaccessible")

    def Mul100(self, i):
      return i * 100


class MockUninitializableTest(absltest.TestCase):

  def testMockNativeNoCtor(self):
    with mock.patch.object(PseudoModule, "NativeNoCtor", autospec=True):
      PseudoModule.NativeNoCtor.return_value.Mul100.return_value = (
          300  # pytype: disable=attribute-error
      )
      obj = PseudoModule.NativeNoCtor()
      self.assertEqual(obj.Mul100(2), 300)
      with self.assertRaises(TypeError):
        # pytype: disable=wrong-arg-count
        obj.Mul100(2, 3)  # pylint: disable=too-many-function-args
        # pytype: enable=wrong-arg-count

  def testMockExtensionNoCtor(self):
    with mock.patch.object(tm, "NoCtor", autospec=True):
      tm.NoCtor.return_value.Mul100.return_value = (
          300  # pytype: disable=attribute-error
      )
      obj = tm.NoCtor()
      self.assertEqual(obj.Mul100(2), 300)
      # UNFORTUNATELY no TypeError from mock here,
      #               pylint also fails to detect this, but
      # FORTUNATELY pytype does (without the directives):
      # pytype: disable=wrong-arg-count
      self.assertEqual(obj.Mul100(2, 3), 300)  # too many positional arguments
      # pytype: enable=wrong-arg-count


class DerivedFromNoCtor(tm.NoCtor):

  def __init__(self):
    pass


class DerivedFromNoCtorTest(absltest.TestCase):

  def testInstantiate(self):
    if tm.__pyclif_codegen_mode__ == "pybind11":
      regex_expected = (
          r"mock_uninitializable\.NoCtor\.__init__\(\) must be called when"
          r" overriding __init__$"
      )
    else:
      regex_expected = (
          r"mock_uninitializable\.NoCtor cannot be used as a base class for a"
          r" Python type because it has no constructor defined \(the derived"
          r" type is \w+\.DerivedFromNoCtor\)\.$"
      )
    with self.assertRaisesRegex(TypeError, regex_expected):
      DerivedFromNoCtor()


if __name__ == "__main__":
  absltest.main()
