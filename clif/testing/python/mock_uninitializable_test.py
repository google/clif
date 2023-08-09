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


class PseudoModule:  # To make this similar to the extension situation.

  class Native:

    def __init__(self):
      raise RuntimeError("Meant to be inaccessible")

    def Mul100(self, i):
      return i * 100


class MockUninitializableTest(absltest.TestCase):

  def testMockNativeType(self):
    with mock.patch.object(PseudoModule, "Native", autospec=True):
      PseudoModule.Native.return_value.Mul100.return_value = 300
      obj = PseudoModule.Native()
      self.assertEqual(obj.Mul100(2), 300)
      with self.assertRaises(TypeError):
        obj.Mul100(2, 3)  # pylint: disable=too-many-function-args

  def testMockExtensionType(self):
    with mock.patch.object(tm, "NoCtor", autospec=True):
      tm.NoCtor.return_value.Mul100.return_value = 300
      obj = tm.NoCtor()
      self.assertEqual(obj.Mul100(2), 300)
      # UNFORTUNATELY no TypeError from mock here,
      #               pylint also fails to detect this:
      self.assertEqual(obj.Mul100(2, 3), 300)  # too many positional arguments


if __name__ == "__main__":
  absltest.main()
