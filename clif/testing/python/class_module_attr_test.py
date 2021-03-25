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


from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import class_module_attr
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import class_module_attr_pybind11
except ImportError:
  class_module_attr_pybind11 = None
# pylint: enable=g-import-not-at-top

EXPECTED_CLASS_MODULE_ATTR_CAPI = (
    'clif.testing.python.class_module_attr')
EXPECTED_CLASS_MODULE_ATTR_PYBIND11 = (
    'clif.testing.python.class_module_attr_pybind11')


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (class_module_attr,
                                             class_module_attr_pybind11))
    if np[1] is not None
])
class ClassModuleAttrTest(absltest.TestCase):

  def testAllTypeOfClasses(self, wrapper_lib):
    if wrapper_lib is class_module_attr:
      expected_class_module_attr = EXPECTED_CLASS_MODULE_ATTR_CAPI
    else:
      expected_class_module_attr = EXPECTED_CLASS_MODULE_ATTR_PYBIND11
    self.assertEqual(wrapper_lib.ConcreteEmpty.__module__,
                     expected_class_module_attr)
    self.assertEqual(wrapper_lib.VirtualBaseEmpty.__module__,
                     expected_class_module_attr)
    self.assertEqual(wrapper_lib.VirtualDerivedEmpty.__module__,
                     expected_class_module_attr)


if __name__ == '__main__':
  absltest.main()
