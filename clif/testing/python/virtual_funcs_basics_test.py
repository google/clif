# Copyright 2020 Google LLC
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

"""Tests for clif.testing.python.virtual_funcs_basics."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import virtual_funcs_basics
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import virtual_funcs_basics_pybind11
except ImportError:
  virtual_funcs_basics_pybind11 = None
# pylint: enable=g-import-not-at-top


class B(virtual_funcs_basics.B):

  def __init__(self):
    virtual_funcs_basics.B.__init__(self)
    self.c = -1

  def set_c(self, v):
    self.c = v


class B_pybind11(virtual_funcs_basics_pybind11.B):  # pylint: disable=invalid-name

  def __init__(self):
    virtual_funcs_basics_pybind11.B.__init__(self)
    self.c = -1

  def set_c(self, v):
    self.c = v


def get_derived_b(wrapper_lib):
  return B_pybind11 if wrapper_lib is virtual_funcs_basics_pybind11 else B


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (virtual_funcs_basics,
                                             virtual_funcs_basics_pybind11))
    if np[1] is not None
])
class VirtualFuncsTest(absltest.TestCase):

  def testBasicCall(self, wrapper_lib):
    b = get_derived_b(wrapper_lib)()
    b.set_c(2)
    self.assertEqual(b.c, 2)
    wrapper_lib.Bset(b, 4)
    self.assertEqual(b.c, 4)

  def testVirtualProperty(self, wrapper_lib):
    c = wrapper_lib.D()
    c.pos_c = -1
    self.assertEqual(c.pos_c, 1)


if __name__ == '__main__':
  absltest.main()
