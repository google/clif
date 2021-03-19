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
from clif.python import pytd2proto

# Use two spaces indentation for generated code.
I = '  '

default_supported_op_types = {'int', 'float', 'double', 'long', 'bool'}

# Dict of python methods that map to C++ operators.
_SPECIAL = pytd2proto._SPECIAL  # pylint: disable=protected-access


def find_operator(s, prefix='::operator'):
  """Use to find the operator in a cpp_name string."""
  index = s.find(prefix)
  if index < 0:
    return -1
  index += len(prefix)
  c = s[index:index + 1]
  if not c or c == '_' or c.isalnum():
    return -1
  return index


def convert_operator_param(param_str: str):
  if param_str in default_supported_op_types:
    return f'{param_str}()'
  else:
    return 'py::self'


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


# Dataclass used to group together and pass around parameter lists.
@dataclasses.dataclass
class ParamsStrings:
  cpp_names: str
  lang_types: str
  names_with_types: str
  default_args: str
