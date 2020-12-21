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
from clif.pybind11 import enums
from clif.pybind11 import utils

I = utils.I


def generate_from(class_decl: ast_pb2.ClassDecl):
  """Generates a complete py::class_<>.

  Args:
    class_decl: Class declaration in proto format.

  Yields:
    pybind11 class bindings code.
  """

  class_name = f'{class_decl.name.native}_class'
  definition = I + f'py::class_<{class_decl.name.cpp_name}'
  for base in class_decl.bases:
    if base.HasField('cpp_name'):
      definition += f', {base.cpp_name}'
  definition += f'> {class_name}(m, "{class_decl.name.native}");'
  yield definition

  for s in _generate_constructors(class_decl, class_name):
    yield I + s

  for member in class_decl.members:
    if member.decltype == ast_pb2.Decl.Type.CONST:
      for s in _generate_const_members(member, class_name):
        yield I + s
    elif member.decltype == ast_pb2.Decl.Type.FUNC:
      for s in _generate_methods(member, class_name):
        yield I + s
    elif member.decltype == ast_pb2.Decl.Type.VAR:
      for s in _generate_variables(class_decl, member, class_name):
        yield I + s
    elif member.decltype == ast_pb2.Decl.Type.ENUM:
      for s in _generate_enums(member, class_name):
        yield I + s


def _generate_constructors(class_decl: ast_pb2.ClassDecl, class_name: str):
  """Generates constructor methods."""
  constructor_defined = False
  for member in class_decl.members:
    if member.decltype == ast_pb2.Decl.Type.FUNC and member.func.name.native == '__init__':
      init_fn = f'{class_name}.def(py::init<'
      params = member.func.params
      for i, param in enumerate(params):
        init_fn += f'{param.type.lang_type}'
        if i != len(params) - 1:
          init_fn += ', '
      init_fn += '>());'
      constructor_defined = True
      yield init_fn

    elif member.decltype == ast_pb2.Decl.Type.FUNC and member.func.constructor:
      fn = f'{class_name}.def_static("{member.func.name.native}", []('
      params = member.func.params
      for i, param in enumerate(params):
        fn += f'{param.type.lang_type} {param.name.cpp_name}'
        if i != len(params) - 1:
          fn += ', '
      fn += f') {{ return {class_decl.name.cpp_name}('
      for i, param in enumerate(params):
        fn += f'{param.name.cpp_name}'
        if i != len(params) - 1:
          fn += ', '
      fn += '); });'
      constructor_defined = True
      yield fn

  if not constructor_defined:
    yield f'{class_name}.def(py::init<>());'


def _generate_const_members(member: ast_pb2.Decl, class_name: str):
  """Generates const member functions."""
  yield (f'{class_name}.def_readonly_static("{member.const.name.native}", '
         f'&{member.const.name.cpp_name});')


def _generate_methods(member: ast_pb2.Decl, class_name: str):
  """Generates methods."""
  if member.func.classmethod:
    yield (f'{class_name}.def_static("{member.func.name.native}", '
           f'&{member.func.name.cpp_name});')
  elif not member.func.constructor:
    yield (f'{class_name}.def("{member.func.name.native}", '
           f'&{member.func.name.cpp_name});')


def _generate_variables(class_decl: ast_pb2.ClassDecl, member: ast_pb2.Decl,
                        class_name: str):
  """Generates variables."""
  # check if it is a var or property
  if member.var.HasField('cpp_get'):
    if member.var.HasField('cpp_set'):
      yield (f'{class_name}.def_property("{member.var.name.native}", '
             f'&{member.var.cpp_get.name.cpp_name}, '
             f'&{member.var.cpp_set.name.cpp_name});')
    else:
      yield (f'{class_name}.def_property_readonly("{member.var.name.native}", '
             f'&{member.var.cpp_get.name.cpp_name});')
  else:
    yield (f'{class_name}.def_readwrite("{member.var.name.native}", '
           f'&{class_decl.name.cpp_name}::{member.var.name.cpp_name});')


def _generate_enums(member: ast_pb2.Decl, class_name: str):
  """Generates enums."""
  for s in enums.generate_from(member.enum, class_name):
    yield s
