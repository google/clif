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

# pylint: disable=line-too-long
"""Basic test for refcount health.

  * get initial refcount of extension type
  * construct N objects
  * assert refcount of extension type >= initial refcount  # SOFT ASSERT
  * delete the N objects
  * assert refcount of extension type == initial refcount  # HARD ASSERT

  The SOFT ASSERT means that the refcount for the extension type may or may
  not be updated when objects of that type are constructed. At the time of
  this writing, either could be considered correct. This may change in the
  future as the Python C API continues to evolve [1].

  Note that the ambituity here adds a motivation to the plan for replacing
  the current PyCLIF code generator with a new generator targeting pybind11
  instead of the Python C API directly. That will allow us to leverage the
  community investments into pybind11 (e.g. [1], [2]) instead of having to
  figure out such highly complex and evolving details independently.

  Related references:
    [1] https://bugs.python.org/issue35810#msg336289
    [2] https://github.com/pybind/pybind11/issues/1946
    [3] https://third_party/pybind11/include/pybind11/detail/class.h?rcl=276599738&l=353

  To see the output of the print statements below, use blaze run, e.g.:

  blaze run -c dbg --copt=-O0 --config=asan //clif/testing/python:extension_type_refcount_test.python3
"""
# pylint: enable=line-too-long

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import gc
import sys
import unittest

import parameterized

from clif.testing.python import extension_type_refcount


# Exercising Python-derived classes because they are currently handled in a
# very interesting way in PyCLIF. With respect to the generated code, the
# `_new()` and `_del()` functions are NOT called. Instead, the `wrapper`
# struct is allocated and zero-initialized from Python C code. The C++
# constructor for the `::clif::Instance` member of `wrapper` is NOT called.
# We're getting "lucky" that this works:
# http://clif/python/gen.py?l=430&rcl=308310543


class PyDerivedConcreteEmpty(extension_type_refcount.ConcreteEmpty):
  pass


class PyDerivedVirtualDerivedEmpty(extension_type_refcount.VirtualDerivedEmpty):
  pass


class ClassModuleAttrTest(unittest.TestCase):

  @parameterized.parameterized.expand([
      (extension_type_refcount.ConcreteEmpty,
       None),
      (extension_type_refcount.VirtualDerivedEmpty,
       None),
      (extension_type_refcount.ConcreteEmpty,
       PyDerivedConcreteEmpty),
      (extension_type_refcount.VirtualDerivedEmpty,
       PyDerivedVirtualDerivedEmpty),
  ])
  def testBasicRefcountHealth(self, ext_type, py_type, num_objs=10000):
    if (py_type is None and sys.version_info.major == 3 and
        sys.version_info.minor >= 8):
      self.skipTest('b/170861151')

    print()
    print('EXT_TYPE:', ext_type)
    print(' PY_TYPE:', py_type)
    if py_type is None:
      py_type = ext_type
    gc.collect()  # Cleanup right before this test (actually needed).
    rc1 = sys.getrefcount(ext_type)
    print('REFCOUNT: %d  INITIAL' % rc1)
    objs = []
    for unused_index in range(num_objs):
      objs.append(py_type())
    rc2 = sys.getrefcount(ext_type)
    print('REFCOUNT: %d  AFTER CONSTRUCTING %d OBJECTS' % (rc2, num_objs))
    del objs
    # Not really needed. Here just to ensure it doesn't break anything.
    gc.collect()
    rc3 = sys.getrefcount(ext_type)
    print('REFCOUNT: %d  AFTER DELETING THE OBJECTS' % rc3)
    self.assertGreaterEqual(rc2, rc1)
    self.assertEqual(rc3, rc1)


if __name__ == '__main__':
  unittest.main()
