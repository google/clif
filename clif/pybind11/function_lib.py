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

"""Common utility functions for pybind11 function code generation."""
import re
from typing import Optional

from clif.protos import ast_pb2
from clif.pybind11 import utils


def num_unknown_default_values(func_decl: ast_pb2.FuncDecl) -> int:
  num_unknown = 0
  for param in func_decl.params:
    if param.default_value == 'default':
      num_unknown += 1
  return num_unknown


def generate_function_suffixes(func_decl: ast_pb2.FuncDecl) -> str:
  """Generates py_args, docstrings and return value policys."""
  py_args = generate_py_args(func_decl)
  suffix = ''
  if py_args:
    suffix += f'{py_args}, '
  suffix += f'{generate_return_value_policy(func_decl)}'
  if func_decl.docstring:
    suffix += f', {generate_docstring(func_decl)}'
  suffix += ');'
  return suffix


def generate_param_type(param: ast_pb2.ParamDecl) -> str:
  if param.type.HasField('callable'):
    return generate_callback_signature(param)
  else:
    return param.type.cpp_type


def generate_def(func_decl: ast_pb2.FuncDecl) -> str:
  static_str = '_static' if func_decl.classmethod else ''
  return f'def{static_str}'


def generate_cpp_function_cast(
    func_decl: ast_pb2.FuncDecl,
    class_decl: Optional[ast_pb2.ClassDecl] = None) -> str:
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
    if param.type.HasField('callable'):
      params_list_types.append(generate_callback_signature(param))
    elif not utils.is_usable_cpp_exact_type(param.cpp_exact_type):
      params_list_types.append(param.type.cpp_type)
    else:
      params_list_types.append(param.cpp_exact_type)
  for ret in func_decl.returns[1:]:
    if not utils.is_usable_cpp_exact_type(ret.cpp_exact_type):
      params_list_types.append(ret.type.cpp_type)
    else:
      params_list_types.append(ret.cpp_exact_type)
  params_str_types = ', '.join(params_list_types)

  return_type = ''
  if func_decl.cpp_void_return:
    return_type = 'void'
  elif func_decl.returns:
    return_type = func_decl.returns[0].cpp_exact_type
  if not return_type:
    return_type = 'void'

  class_sig = ''
  if class_decl and not (func_decl.cpp_opfunction or
                         func_decl.is_extend_method or
                         func_decl.classmethod):
    class_sig = f'{class_decl.name.cpp_name}::'
    if func_decl.postproc == '->self' and func_decl.ignore_return_value:
      return_type = class_decl.name.cpp_name

  cpp_const = ''
  if func_decl.cpp_const_method:
    cpp_const = ' const'
  return f'({return_type} ({class_sig}*)({params_str_types}){cpp_const})'


def generate_callback_signature(param: ast_pb2.ParamDecl) -> str:
  """Generate signatures for callback functions."""
  func_decl = param.type.callable
  params_list_types = []
  for param in func_decl.params:
    params_list_types.append(param.cpp_exact_type)
  params_str_types = ', '.join(params_list_types)
  if func_decl.cpp_void_return:
    return_type = 'void'
  elif func_decl.returns:
    return_type = func_decl.returns[0].cpp_exact_type
  return f'::std::function<{return_type}({params_str_types})>'


def generate_py_args(func_decl: ast_pb2.FuncDecl) -> str:
  """Generates bindings code for function parameter declarations."""
  params_list = []
  for param in func_decl.params:
    if param.name.native == 'self' or param.name.native == 'cls':
      continue
    cpp_name = param.name.cpp_name
    if param.default_value and param.default_value != 'default':
      params_list.append(
          f'py::arg("{cpp_name}") = static_cast<{param.type.cpp_type}>'
          f'({param.default_value})')
    else:
      params_list.append(f'py::arg("{cpp_name}")')
  return ', '.join(params_list)


def generate_docstring(func_decl: ast_pb2.FuncDecl) -> str:
  docstring = func_decl.docstring.strip().replace('\n', r'\n').replace(
      '"', r'\"')
  return f'"{docstring}"'


def generate_return_value_policy(func_decl: ast_pb2.FuncDecl) -> str:
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
  # For smart pointers, it is unnecessary to specify a return value policy in
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
