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
"""Generates pybind11 bindings code for constants."""

from clif.protos import ast_pb2
from clif.pybind11 import function_lib
from clif.pybind11 import utils

I = utils.I


def generate_from(class_name: str, const_decl: ast_pb2.ConstDecl):
  """Generates bindings code for constants."""
  return_value_policy = ''

  # Legacy CLIF ignores postconversion for clif::char_ptr.
  if (function_lib.is_bytes_type(const_decl.type)
      and const_decl.type.cpp_type != '::clif::char_ptr'):
    return_value_policy = ', py::return_value_policy::_return_as_bytes'
  yield I + (f'{class_name}.attr("{const_decl.name.native}") = '
             f'py::cast(static_cast<{const_decl.type.cpp_type}>('
             f'{const_decl.name.cpp_name}){return_value_policy});')
