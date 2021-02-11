# Copyright 2017 Google Inc.
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

"""Tests for clif.testing.python.templates."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import templates
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import templates_pybind11
except ImportError:
  templates_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (templates, templates_pybind11))
    if np[1] is not None
])
class TemplatesTest(absltest.TestCase):

  @absltest.skip('NEEDS_SMART_HOLDER')
  def testTemplates(self, wrapper_lib):
    a = wrapper_lib.A()
    wrapper_lib.TemplateParamFunc(a)

  def testTemplateClassInstantiation(self, wrapper_lib):
    # The instantiation of the class should not blow up.
    wrapper_lib.TemplateClassInt()

  def testTypedefInTemplateClass(self, wrapper_lib):
    b = wrapper_lib.VectorHolder()
    self.assertEqual(b.MethodUsingTemplateType(b), 1)

if __name__ == '__main__':
  absltest.main()
