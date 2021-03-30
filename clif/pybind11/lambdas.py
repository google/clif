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

"""Generates C++ lambda functions inside pybind11 bindings code."""

from clif.protos import ast_pb2
from clif.pybind11 import utils

I = utils.I


def generate_lambda_if_needed(func_decl: ast_pb2.FuncDecl, module_name: str):
  if _func_has_return_param(func_decl):
    yield from _generate_return_args_lambda(func_decl, module_name)
    return

  if _has_bytes_return(func_decl):
    yield from _generate_cpp_lambda(func_decl, 'py::bytes',
                                    module_name)
    return


def _func_has_return_param(func_decl) -> bool:
  return len(func_decl.returns) >= 2 or (len(func_decl.returns) == 1 and
                                         func_decl.cpp_void_return and
                                         len(func_decl.params) >= 1)


def _generate_cpp_lambda(func_decl: ast_pb2.FuncDecl, return_type: str,
                         class_name: str):
  """Generates C++ lambda functions."""

  params_strings = utils.get_params_strings_from_func_decl(func_decl)

  static = ''
  if func_decl.classmethod:
    static = '_static'

  yield I + f'{class_name}.def{static}("{func_decl.name.native}",'
  yield I + I + f'[]({params_strings.names_with_types}) -> {return_type} {{'
  yield I + I + I + ('return '
                     f'{func_decl.name.cpp_name}({params_strings.cpp_names});')
  yield I + I + '}'
  yield I + ');'


def _generate_return_args_lambda(func_decl: ast_pb2.FuncDecl, module_name: str):
  """Generates C++ lambda functions with return parameters."""

  params_strings = utils.get_params_strings_from_func_decl(func_decl)

  yield (f'{module_name}.def("{func_decl.name.native}",'
         f'[]({params_strings.names_with_types}) {{')

  main_return = ''
  main_return_cpp_name = ''
  other_returns_cpp_names = []
  for i, r in enumerate(func_decl.returns):
    if i == 0:
      main_return_cpp_name = r.name.cpp_name
      main_return = f'{r.type.cpp_type} {r.name.cpp_name}'
      continue
    other_returns_cpp_names.append(r.name.cpp_name)
    yield I + f'{r.type.cpp_type} {r.name.cpp_name};'
  other_returns = ', '.join(other_returns_cpp_names)
  other_returns_params_list = [f'&{r}' for r in other_returns_cpp_names]

  if not func_decl.cpp_void_return:
    yield I + (f'{main_return} = {func_decl.name.cpp_name}'
               f'({params_strings.cpp_names}, &y);')
    yield I + (f'return std::make_tuple({main_return_cpp_name}, '
               f'{other_returns});')
  else:
    yield I + f'{main_return};'
    if not other_returns_cpp_names:
      yield I + (f'{func_decl.name.cpp_name}({params_strings.cpp_names},'
                 f'&{main_return_cpp_name});')
      yield I + f'return {main_return_cpp_name};'
    else:
      yield I + (f'{func_decl.name.cpp_name}({params_strings.cpp_names},'
                 f'&{main_return_cpp_name}, {other_returns_params_list});')
      yield I + (f'return std::make_tuple({main_return_cpp_name}, '
                 f'{other_returns});')
  yield '});'


def _has_bytes_return(func_decl: ast_pb2.FuncDecl):
  for r in func_decl.returns:
    if r.HasField('type'):
      if r.type.lang_type == 'bytes':
        return True
  return False
