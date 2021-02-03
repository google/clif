# Copyright 2021 Google LLC
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

"""Tests for clif.pybind11.staging.templates.

This file is a copy of clif/testing/python/templates_test.py.
"""

import unittest
from clif.pybind11.staging import templates


class TemplatesTest(unittest.TestCase):

  @unittest.skip(
      'Pybind11 does not support using unique pointers as function arguments')
  def testTemplates(self):
    a = templates.A()
    templates.TemplateParamFunc(a)

  def testTemplateClassInstantiation(self):
    # The instantiation of the class should not blow up.
    templates.TemplateClassInt()

  def testTypedefInTemplateClass(self):
    b = templates.VectorHolder()
    self.assertEqual(b.MethodUsingTemplateType(b), 1)

if __name__ == '__main__':
  unittest.main()
