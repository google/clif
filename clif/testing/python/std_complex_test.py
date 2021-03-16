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


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (std_complex, std_complex_pybind11))
    if np[1] is not None
])
class StdComplexTest(absltest.TestCase):

  def testZero(self, wrapper_lib):
    self.assertAlmostEqual(wrapper_lib.StdComplexFloat.Zero(), complex(0))
    self.assertAlmostEqual(wrapper_lib.StdComplexDouble.Zero(), complex(0))

  def testOne(self, wrapper_lib):
    self.assertAlmostEqual(wrapper_lib.StdComplexFloat.One(), complex(1))
    self.assertAlmostEqual(wrapper_lib.StdComplexDouble.One(), complex(1))

  def testI(self, wrapper_lib):
    self.assertAlmostEqual(wrapper_lib.StdComplexFloat.i(), 1j)
    self.assertAlmostEqual(wrapper_lib.StdComplexDouble.i(), 1j)

  def testMultiply(self, wrapper_lib):
    self.assertAlmostEqual(
        wrapper_lib.StdComplexFloat.Multiply(wrapper_lib.StdComplexFloat.i(),
                                             wrapper_lib.StdComplexFloat.i()),
        -wrapper_lib.StdComplexFloat.One())
    self.assertAlmostEqual(
        wrapper_lib.StdComplexDouble.Multiply(wrapper_lib.StdComplexDouble.i(),
                                              wrapper_lib.StdComplexDouble.i()),
        -wrapper_lib.StdComplexDouble.One())


if __name__ == '__main__':
  absltest.main()
