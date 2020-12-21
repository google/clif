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
"""Generates pybind11 bindings code for classes."""

from clif.protos import ast_pb2
from clif.pybind11 import utils

I = utils.I


def generate_from(enum_decl: ast_pb2.EnumDecl, class_str: str):
  """Generates enums."""
  enum_def = I + (f'py::enum_<{enum_decl.name.cpp_name}>({class_str}, '
                  f'"{enum_decl.name.native}")')
  members = enum_decl.members
  for member in members:
    enum_def += '\n' + I + I + f'.value("{member.native}", {member.cpp_name})'

  if not enum_decl.enum_class:
    enum_def += '\n' + I + I + '.export_values()'

  enum_def += ';'
  yield enum_def
