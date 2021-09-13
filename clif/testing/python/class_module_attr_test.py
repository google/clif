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

from clif.testing.python import class_module_attr

EXPECTED_CLASS_MODULE_ATTR = (
    'clif.testing.python.class_module_attr')


class ClassModuleAttrTest(absltest.TestCase):

  def testAllTypeOfClasses(self):
    self.assertEqual(class_module_attr.ConcreteEmpty.__module__,
                     EXPECTED_CLASS_MODULE_ATTR)
    self.assertEqual(class_module_attr.VirtualBaseEmpty.__module__,
                     EXPECTED_CLASS_MODULE_ATTR)
    self.assertEqual(class_module_attr.VirtualDerivedEmpty.__module__,
                     EXPECTED_CLASS_MODULE_ATTR)


if __name__ == '__main__':
  absltest.main()
