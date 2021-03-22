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

"""Tests for clif.testing.python.default_args."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import default_args
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import default_args_pybind11
except ImportError:
  default_args_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np
    for np in zip(('c_api', 'pybind11'), (default_args, default_args_pybind11))
    if np[1] is not None
])
class DefaultArgsTest(absltest.TestCase):

  def testDefaultArgs(self, wrapper_lib):
    a = wrapper_lib.MyClass()
    with self.assertRaises(ValueError):
      a.MethodWithDefaultClassArg(i=113)
    self.assertEqual(a.MethodWithDefaultEnumArg(i=5000), 5432)
    self.assertEqual(a.MethodWithDefaultPtrArg(i=1234), 1234)
    self.assertEqual(a.MethodWithDefaultFlag(i=32), 35)
    self.assertEqual(a.MethodThrowAwayDefault(input1=1, input2=2), 3)
    # Invoking methods that ignore the return values should not blow up.
    a.MethodThrowAwayDefault2(input1=1, input2=2)
    a.MethodWithOutputDefault3(input1=123, input2=456)
    self.assertEqual(a.MethodWithOutputDefault4(), 1000)
    self.assertEqual(a.MethodWithOutputDefault5(input1=10), 1000)
    a.MethodWithOutputDefault6()
    a.MethodWithOutputDefault7(input1=10)
    a.MethodWithOutputDefault8()

if __name__ == '__main__':
  absltest.main()
