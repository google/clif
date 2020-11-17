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

"""Generates pybind11 bindings code for functions."""

from typing import Sequence, Text

from clif.protos import ast_pb2
from clif.pybind11 import utils


I = utils.I


def generate_from(func_decl: ast_pb2.FuncDecl):
  """Generates pybind11 bindings code for functions.

  Args:
    func_decl: Function declaration in proto format.

  Yields:
    pybind11 function bindings code.
  """
  func_def = I+f'm.def("{func_decl.name.native}", &{func_decl.name.cpp_name}'
  if func_decl.params:
    func_def += f', {_generate_params_list(func_decl.params)}'
  if func_decl.docstring:
    func_def += f', {_generate_docstring(func_decl.docstring)}'
  func_def += ');'
  yield func_def


def _generate_params_list(params: Sequence[ast_pb2.ParamDecl]) -> Text:
  """Generates bindings code for function parameters."""
  params_list = ''
  for i, param in enumerate(params):
    cpp_name = param.name.cpp_name
    if param.default_value:
      params_list += f'py::arg("{cpp_name}") = {param.default_value}'
    else:
      params_list += f'py::arg("{cpp_name}")'
    if i != len(params) - 1:
      params_list += ', '
  return params_list


def _generate_docstring(docstring: Text):
  if docstring:
    docstring = docstring.strip().replace('\n', r'\n').replace('"', r'\"')
    return f'"{docstring}"'
  return '""'
