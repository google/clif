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

"""Tests for clif.testing.python.classes."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import classes
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import classes_pybind11
except ImportError:
  classes_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (classes, classes_pybind11))
    if np[1] is not None
])
class ClassesTest(absltest.TestCase):

  def testKlass(self, wrapper_lib):
    self.assertEqual(wrapper_lib.Klass.C2(), 3)
    k = wrapper_lib.Klass(3)
    self.assertEqual(k.i, 3)
    self.assertEqual(k.i2, 9)
    self.assertEqual(k.Int1(), 4)
    k.i = 0
    self.assertEqual(k.i, 0)
    # AttributeError on CPython; TypeError on PyPy.
    with self.assertRaises((AttributeError, TypeError)):
      k.i2 = 0

  def testDerivedClassDocstring(self, wrapper_lib):
    # Nothing special about this being a derived class; that is just the
    # one our test .clif file has a docstring on.
    self.assertIn('class also has a docstring.\n\n',
                  wrapper_lib.Derived.__doc__)
    self.assertIn('spans multiple lines', wrapper_lib.Derived.__doc__)
    self.assertIn(wrapper_lib.Derived.__doc__,
                  wrapper_lib.Derived.__doc__.strip())

  def testPythonDerived(self, wrapper_lib):
    class PyK(wrapper_lib.Klass):
      pass
    k = PyK(4)
    self.assertEqual(k.i, 4)
    self.assertEqual(k.Int1(), 5)

  def testDerived(self, wrapper_lib):
    #    k = wrapper_lib.Derived()
    k = wrapper_lib.Derived.Init(0, 0)
    self.assertEqual(k.i, 0)
    self.assertEqual(k.j, 0)
    self.assertNotIn(2, k)
    with self.assertRaises(TypeError):
      wrapper_lib.Derived(1)

  def testDerivedInit(self, wrapper_lib):
    k = wrapper_lib.Derived.Init(1, 2)
    self.assertEqual(k.i, 1)
    self.assertEqual(k.j, 2)


if __name__ == '__main__':
  absltest.main()
