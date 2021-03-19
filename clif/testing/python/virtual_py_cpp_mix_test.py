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
from absl.testing import parameterized

from clif.testing.python import virtual_py_cpp_mix
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import virtual_py_cpp_mix_pybind11
except ImportError:
  virtual_py_cpp_mix_pybind11 = None
# pylint: enable=g-import-not-at-top


class PyDerived(virtual_py_cpp_mix.Base):

  def __init__(self):
    virtual_py_cpp_mix.Base.__init__(self)

  def Get(self):
    return 323


class PyDerivedPybind11(virtual_py_cpp_mix_pybind11.Base):

  def __init__(self):
    virtual_py_cpp_mix_pybind11.Base.__init__(self)

  def Get(self):
    return 323


def GetPyDerived(wrapper_lib):
  if wrapper_lib is virtual_py_cpp_mix:
    return PyDerived
  return PyDerivedPybind11


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (virtual_py_cpp_mix,
                                             virtual_py_cpp_mix_pybind11))
    if np[1] is not None
])
class VirtualPyCppMixTest(absltest.TestCase):

  def testPyDerivedGet(self, wrapper_lib):
    d = GetPyDerived(wrapper_lib)()
    self.assertEqual(d.Get(), 323)

  def testGetFromCppPlaincPtrPassingPyDerived(self, wrapper_lib):
    d = GetPyDerived(wrapper_lib)()
    self.assertEqual(wrapper_lib.GetFromCppPlaincPtr(d), 4323)

  def testGetFromCppUniquePtrPassingPyDerived(self, wrapper_lib):
    d = GetPyDerived(wrapper_lib)()
    self.assertEqual(wrapper_lib.GetFromCppUniquePtr(d), 5323)

  def testCppDerivedGet(self, wrapper_lib):
    d = wrapper_lib.CppDerived()
    if wrapper_lib is virtual_py_cpp_mix:
      expected = 101  # NOT GOOD, but this will be fixed in the switch to ...
    else:
      expected = 212  # ... pybind11, because this result is correct.
    self.assertEqual(d.Get(), expected)

  def testGetFromCppPlaincPtrPassingCppDerived(self, wrapper_lib):
    d = wrapper_lib.CppDerived()
    self.assertEqual(wrapper_lib.GetFromCppPlaincPtr(d), 4212)

  def testGetFromCppUniquePtrPassingCppDerived(self, wrapper_lib):
    d = wrapper_lib.CppDerived()
    self.assertEqual(wrapper_lib.GetFromCppUniquePtr(d), 5212)


if __name__ == '__main__':
  absltest.main()
