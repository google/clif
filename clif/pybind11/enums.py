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
"""Generates pybind11 bindings code for enums."""

from clif.protos import ast_pb2
from clif.pybind11 import utils

I = utils.I


def generate_from(class_name: str, enum_decl: ast_pb2.EnumDecl):
  """Generates enums."""
  kind = 'Enum' if enum_decl.enum_class else 'IntEnum'
  yield I + (
      f'{class_name} += py::native_enum<{enum_decl.name.cpp_name}>'
      f'("{enum_decl.name.native}", py::native_enum_kind::{kind})'
  )
  for i, member in enumerate(enum_decl.members):
    s = I + I + f'.value("{member.native}", {member.cpp_name})'
    if i == len(enum_decl.members) - 1:
      s += ';'
    yield s
