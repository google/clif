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

import re
from typing import Sequence, Text, Optional

from clif.protos import ast_pb2
from clif.pybind11 import lambdas
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

  lambda_generated = False
  for s in lambdas.generate_lambda(func_decl, module_name, class_decl):
    yield s
    if s:
      lambda_generated = True
  if lambda_generated:
    return

  if func_decl.classmethod:
    for line in _generate_static_method(module_name, func_decl.name.native,
                                        func_decl.name.cpp_name):
      yield I + line
    return

  if operators.needs_operator_overloading(func_decl):
    yield from operators.generate_operator(module_name, func_decl)
  else:
    func_name = utils.format_func_name(func_decl.name.native)
    func_def = I + f'{module_name}.def("{func_name}", '
    func_def += _generate_cpp_function_cast(func_decl, class_decl)
    func_def += f'&{func_decl.name.cpp_name}'
    if func_decl.params:
      func_def += _generate_params_list(func_decl.params,
                                        func_decl.is_extend_method)
    func_def += f', {_generate_return_value_policy(func_decl)}'
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
      if not utils.is_usable_cpp_exact_type(param.cpp_exact_type):
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


def _generate_static_method(class_name: str, func_name_native: str,
                            func_name_cpp_name: str):
  yield (f'{class_name}.def_static("{func_name_native}", '
         f'&{func_name_cpp_name});')


def _generate_return_value_policy(func_decl: ast_pb2.FuncDecl) -> Text:
  """Generates pybind11 return value policy based on function return type.

  Emulates the behavior of the generated Python C API code.

  Args:
    func_decl: The function declaration that needs to be processed.

  Returns:
    pybind11 return value policy based on the function return value.
  """
  prefix = 'py::return_value_policy::'
  if func_decl.cpp_void_return or not func_decl.returns:
    return prefix + 'automatic'
  return_type = func_decl.returns[0]
  # For smart pointers, it is unncessary to specify a return value policy in
  # pybind11.
  if re.match('::std::unique_ptr<.*>', return_type.cpp_exact_type):
    return prefix + 'automatic'
  elif re.match('::std::shared_ptr<.*>', return_type.cpp_exact_type):
    return prefix + 'automatic'
  elif return_type.type.cpp_raw_pointer:
    # Const pointers to uncopyable object are not supported by PyCLIF.
    if return_type.cpp_exact_type.startswith('const '):
      return prefix + 'copy'
    else:
      return prefix + 'reference'
  elif return_type.cpp_exact_type.endswith('&'):
    if return_type.cpp_exact_type.startswith('const '):
      return prefix + 'copy'
    elif return_type.type.cpp_movable:
      return prefix + 'move'
    else:
      return prefix + 'automatic'
  else:  # Function returns objects directly.
    if return_type.type.cpp_movable:
      return prefix + 'move'
    elif return_type.type.cpp_copyable:
      return prefix + 'copy'
  return prefix + 'automatic'
