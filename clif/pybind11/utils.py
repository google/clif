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
from typing import Dict, Set

from clif.protos import ast_pb2


# Use two spaces indentation for generated code.
I = '  '


@dataclasses.dataclass
class CodeGenInfo:
  """Wrapper of the information needed to generate pybind11 code."""

  # A set of C++ types that are defined as capsules.
  capsule_types: Set[str]

  # Is type caster of `absl::Status` required?
  requires_status: bool

  # What C++ types do we need to generate `pybind11::dynamic_attr()`?
  # This is needed because if we generate `pybind11::dynamic_attr()` for the
  # base class, we also need to generate `pybind11::dynamic_attr()` for the
  # derived class.
  dynamic_attr_types: Set[str]

  # Dict[Python Name, Fully qualified Python name]
  namemap: Dict[str, str]


# Do a SWIG-like name mangling.
def generate_mangled_name_for_module(full_dotted_module_name: str) -> str:
  """Converts `third_party.py.module` to `third__party_py_module`."""
  return full_dotted_module_name.replace('_', '__').replace('.', '_')


def trampoline_name(class_decl: ast_pb2.ClassDecl) -> str:
  return f'{class_decl.name.native}_trampoline'


def is_nested_template(s: str) -> bool:
  # This function works around CLIF matcher bug b/118736768:
  # cpp_exact_type is incorrect for nested templates.
  # This is a crude stop-gap way of unblocking development
  # work for now.
  return '>>' in s


def is_usable_cpp_exact_type(s: str) -> bool:
  return not is_nested_template(s) or '&' in s
