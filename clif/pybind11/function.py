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

from typing import Sequence, Text, Optional

from clif.protos import ast_pb2
from clif.pybind11 import operators
from clif.pybind11 import utils


I = utils.I


def generate_from(module_name: str, func_decl: ast_pb2.FuncDecl,
                  class_decl: Optional[ast_pb2.ClassDecl]):
  """Generates pybind11 bindings code for functions.

  Args:
    module_name: String containing the superclass name.
    func_decl: Function declaration in proto format.
    class_decl: Outer class declaration in proto format. None if the function is
      not a member of a class.

  Yields:
    pybind11 function bindings code.
  """

  operator_index = utils.find_operator(func_decl.name.cpp_name)
  if operator_index >= 0 and func_decl.cpp_opfunction:
    for s in operators.generate_operator(module_name, func_decl,
                                         operator_index):
      yield I + s
      return

  func_def = I + f'{module_name}.def("{func_decl.name.native}", '
  func_def += _generate_cpp_function_cast(func_decl, class_decl)
  func_def += f'&{func_decl.name.cpp_name}'
  if func_decl.params:
    func_def += f', {_generate_params_list(func_decl.params)}'
  if func_decl.docstring:
    func_def += f', {_generate_docstring(func_decl.docstring)}'
  func_def += ');'
  yield func_def


def _generate_cpp_function_cast(func_decl: ast_pb2.FuncDecl,
                                class_decl: Optional[ast_pb2.ClassDecl]):
  """Generates a method signature for each function.

  Args:
    func_decl: Function declaration in proto format.
    class_decl: Outer class declaration in proto format. None if the function is
      not a member of a class.

  Returns:
    The signature of the function.
  """

  params_list_types = []
  for param in func_decl.params:
    if param.HasField('cpp_exact_type'):
      params_list_types.append(param.cpp_exact_type)
  params_str_types = ', '.join(params_list_types)

  return_type = ''
  if func_decl.cpp_void_return:
    return_type = 'void'
  elif func_decl.returns:
    for v in func_decl.returns:
      # There can be only one returns declaration per function.
      if v.HasField('cpp_exact_type'):
        return_type = v.cpp_exact_type
  if not return_type:
    return_type = 'void'

  class_sig = ''
  if class_decl and not func_decl.cpp_opfunction:
    class_sig = f'{class_decl.name.cpp_name}::'
    if func_decl.postproc == '->self' and func_decl.ignore_return_value:
      return_type = class_decl.name.cpp_name

  cpp_const = ''
  if func_decl.cpp_const_method:
    cpp_const = ' const'
  return f'({return_type} ({class_sig}*)({params_str_types}){cpp_const})'


def _generate_params_list(params: Sequence[ast_pb2.ParamDecl]) -> Text:
  """Generates bindings code for function parameters."""
  params_list = ''
  for i, param in enumerate(params):
    cpp_name = param.name.cpp_name
    if cpp_name == 'this':
      continue
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
