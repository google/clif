# Lint as: python3
"""Tests for testing.python.std_complex."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


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
