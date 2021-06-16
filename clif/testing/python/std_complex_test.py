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

"""Tests for testing.python.std_complex."""


from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import std_complex
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import std_complex_pybind11
except ImportError:
  std_complex_pybind11 = None
# pylint: enable=g-import-not-at-top


def MakeNamedParameters():
  np = []
  for code_gen, wrapper_lib in (('c_api', std_complex),
                                ('pybind11', std_complex_pybind11)):
    if wrapper_lib is not None:
      for precision, complex_typename in (('float', 'StdComplexFloat'),
                                          ('double', 'StdComplexDouble')):
        np.append(('_'.join((precision, code_gen)),
                   getattr(wrapper_lib, complex_typename)))
  return np


@parameterized.named_parameters(MakeNamedParameters())
class StdComplexTest(absltest.TestCase):

  def testZero(self, complex_type):
    self.assertAlmostEqual(complex_type.Zero(), complex(0))

  def testOne(self, complex_type):
    self.assertAlmostEqual(complex_type.One(), complex(1))

  def testI(self, complex_type):
    self.assertAlmostEqual(complex_type.i(), 1j)

  def testMultiply(self, complex_type):
    self.assertAlmostEqual(
        complex_type.Multiply(complex_type.i(), complex_type.i()),
        -complex_type.One())


if __name__ == '__main__':
  absltest.main()
