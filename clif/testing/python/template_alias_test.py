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

"""Tests for clif.testing.python.template_alias."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import template_alias
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import template_alias_pybind11
except ImportError:
  template_alias_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (template_alias,
                                             template_alias_pybind11))
    if np[1] is not None
])
class TemplateAliasTest(absltest.TestCase):

  def testTemplateAlias(self, wrapper_lib):
    # Calling the following functions should not blow up.
    wrapper_lib.func_default_vector_input([])
    output = wrapper_lib.func_default_vector_output()
    self.assertLen(output, 1)
    self.assertEqual(output[0], 123)
    return_list = wrapper_lib.func_default_vector_return()
    self.assertLen(return_list, 1)
    self.assertEqual(return_list[0], 100)
    wrapper_lib.func_clif_vector([1])
    wrapper_lib.func_signed_size_type_output()


if __name__ == '__main__':
  absltest.main()
