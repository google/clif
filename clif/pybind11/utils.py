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

"""Utility functions for pybind11 code generator."""

import dataclasses
from clif.protos import ast_pb2
from clif.python import pytd2proto

# Use two spaces indentation for generated code.
I = '  '

# Dict of python methods that map to C++ operators.
_SPECIAL = pytd2proto._SPECIAL  # pylint: disable=protected-access


def format_func_name(name: str):
  if name.endswith('__#'):
    return name[:-1]
  return name


def is_special_operation(s) -> bool:
  if s.endswith('__#'):
    s = s[:-1]
  return s in _SPECIAL


def is_nested_template(s: str) -> bool:
  # This function works around CLIF matcher bug b/118736768:
  # cpp_exact_type is incorrect for nested templates.
  # This is a crude stop-gap way of unblocking development
  # work for now.
  return '>>' in s


def is_usable_cpp_exact_type(s: str) -> bool:
  return not is_nested_template(s) or '&' in s


def get_params_strings_from_func_decl(func: ast_pb2.FuncDecl):
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
        f'{param.type.cpp_type} {param.name.cpp_name}')
    if param.default_value:
      default_values.append(
          f'py::arg("{param.name.cpp_name}") = {param.default_value}')
    else:
      default_values.append(f'py::arg("{param.name.cpp_name}")')

  result = ParamsStrings(
      cpp_names=', '.join(cpp_names),
      lang_types=', '.join(lang_types),
      names_with_types=', '.join(params_str_with_types_list),
      default_args=', '.join(default_values))
  return result


# Dataclass used to group together and pass around parameter lists.
@dataclasses.dataclass
class ParamsStrings:
  cpp_names: str
  lang_types: str
  names_with_types: str
  default_args: str
