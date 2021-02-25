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

  if func_decl.classmethod:
    for line in _generate_static_method(module_name, func_decl.name.native,
                                        func_decl.name.cpp_name):
      yield I + line
    return

  operator_index = utils.find_operator(func_decl.name.cpp_name)
  if operator_index >= 0 and utils.is_special_operation(func_decl.name.native):
    for s in operators.generate_operator(module_name, func_decl,
                                         operator_index):
      yield I + s
      return

  func_name = utils.format_func_name(func_decl.name.native)
  func_def = I + f'{module_name}.def("{func_name}", '
  func_def += _generate_cpp_function_cast(func_decl, class_decl)
  func_def += f'&{func_decl.name.cpp_name}'
  if func_decl.params:
    func_def += _generate_params_list(func_decl.params,
                                      func_decl.is_extend_method)
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
      if utils.is_nested_template(param.cpp_exact_type):
        params_list_types.append(param.type.cpp_type)
      else:
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
  if class_decl and not (func_decl.cpp_opfunction or
                         func_decl.is_extend_method):
    class_sig = f'{class_decl.name.cpp_name}::'
    if func_decl.postproc == '->self' and func_decl.ignore_return_value:
      return_type = class_decl.name.cpp_name

  cpp_const = ''
  if func_decl.cpp_const_method:
    cpp_const = ' const'
  return (f'\n{I + I}({return_type} ({class_sig}*)'
          f'\n{I + I}({params_str_types}){cpp_const})'
          f'\n{I + I}')


def _generate_params_list(params: Sequence[ast_pb2.ParamDecl],
                          is_extend_method: bool) -> Text:
  """Generates bindings code for function parameters."""
  params_list = []
  for i, param in enumerate(params):
    cpp_name = param.name.cpp_name
    if cpp_name == 'this' or (i == 0 and is_extend_method):
      continue
    if param.default_value:
      params_list.append(f'py::arg("{cpp_name}") = {param.default_value}')
    else:
      params_list.append(f'py::arg("{cpp_name}")')
  if params_list:
    return ', ' + ', '.join(params_list)
  return ''


def _generate_docstring(docstring: Text):
  if docstring:
    docstring = docstring.strip().replace('\n', r'\n').replace('"', r'\"')
    return f'"{docstring}"'
  return '""'


def get_params_strings(func: ast_pb2.FuncDecl):
  """Helper for function parameter formatting."""

  params = func.params
  lang_types = []
  cpp_names = []
  params_str_with_types_list = []
  default_values = []

  for param in params:
    lang_types.append(param.type.lang_type)
    cpp_names.append(param.name.cpp_name)
    params_str_with_types_list.append(
        f'{param.type.lang_type} {param.name.cpp_name}')
    if param.default_value:
      default_values.append(
          f'py::arg("{param.name.cpp_name}") = {param.default_value}')
    else:
      default_values.append(f'py::arg("{param.name.cpp_name}")')

  result = utils.ParamsStrings(
      cpp_names=', '.join(cpp_names),
      lang_types=', '.join(lang_types),
      names_with_types=', '.join(params_str_with_types_list),
      default_args=', '.join(default_values))
  return result


def _generate_static_method(class_name: str, func_name_native: str,
                            func_name_cpp_name: str):
  yield (f'{class_name}.def_static("{func_name_native}", '
         f'&{func_name_cpp_name});')
