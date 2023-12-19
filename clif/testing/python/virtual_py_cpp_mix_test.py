# Copyright 2021 Google LLC
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

from clif.testing.python import virtual_py_cpp_mix


class PyDerived(virtual_py_cpp_mix.Base):

  def __init__(self):
    virtual_py_cpp_mix.Base.__init__(self)

  def Get(self):
    return 323


class VirtualPyCppMixTest(absltest.TestCase):

  def testPyDerivedGet(self):
    d = PyDerived()
    self.assertEqual(d.Get(), 323)

  def testGetFromCppPlaincPtrPassingPyDerived(self):
    d = PyDerived()
    self.assertEqual(virtual_py_cpp_mix.GetFromCppPlaincPtr(d), 4323)

  def testGetFromCppUniquePtrPassingPyDerived(self):
    d = PyDerived()
    self.assertEqual(virtual_py_cpp_mix.GetFromCppUniquePtr(d), 5323)

  def testCppDerivedGet(self):
    d = virtual_py_cpp_mix.CppDerived()
    if virtual_py_cpp_mix.__pyclif_codegen_mode__ == 'pybind11':
      expected = 212  # NOT GOOD, but this will be fixed in the switch to ...
    else:
      expected = 101  # ... pybind11, because this result is correct.
    self.assertEqual(d.Get(), expected)

  def testGetFromCppPlaincPtrPassingCppDerived(self):
    d = virtual_py_cpp_mix.CppDerived()
    self.assertEqual(virtual_py_cpp_mix.GetFromCppPlaincPtr(d), 4212)

  def testGetFromCppUniquePtrPassingCppDerived(self):
    d = virtual_py_cpp_mix.CppDerived()
    self.assertEqual(virtual_py_cpp_mix.GetFromCppUniquePtr(d), 5212)


if __name__ == '__main__':
  absltest.main()
