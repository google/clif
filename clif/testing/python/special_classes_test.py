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

"""Tests for clif.testing.python.special_classes."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import special_classes
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import special_classes_pybind11
except ImportError:
  special_classes_pybind11 = None
# pylint: enable=g-import-not-at-top


def expected_exception(wrapper_lib):
  return TypeError if wrapper_lib is special_classes_pybind11 else ValueError


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (special_classes,
                                             special_classes_pybind11))
    if np[1] is not None
])
class SpecialClassesTest(absltest.TestCase):

  def testAbstract(self, wrapper_lib):
    self.assertTrue(wrapper_lib.Abstract.Future)
    self.assertRaises(expected_exception(wrapper_lib), wrapper_lib.Abstract)
    self.assertEqual(wrapper_lib.Abstract.KIND, 'pure virtual',
                     str(type(wrapper_lib.Abstract.KIND)))

  def testInconstructibleStaticMethod(self, wrapper_lib):
    self.assertEqual(wrapper_lib.InconstructibleF(), 0)

  def testNoDefaultConstructor(self, wrapper_lib):
    with self.assertRaises(expected_exception(wrapper_lib)):
      # true error, no def ctor
      _ = wrapper_lib.NoDefaultConstructor().a
    with self.assertRaises(expected_exception(wrapper_lib)):
      # true error, non-def ctor not wrapped
      _ = wrapper_lib.NoDefaultConstructor(1).a

  def testNoCopy(self, wrapper_lib):
    no_copy = wrapper_lib.NoCopy(1)
    self.assertEqual(no_copy.a, 1)

  def testNoMove(self, wrapper_lib):
    no_move = wrapper_lib.NoMove(1)
    self.assertEqual(no_move.a, 1)


if __name__ == '__main__':
  absltest.main()
