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


def generate_from(class_decl: ast_pb2.ClassDecl):
  """Generates a complete py::class_<>.

  Args:
    class_decl: Class declaration in proto format.

  Yields:
    pybind11 class bindings code.
  """

  definition = I + f'py::class_<{class_decl.name.cpp_name}'
  for base in class_decl.bases:
    if base.HasField('cpp_name'):
      definition += f', {base.cpp_name}'
  definition += f'>(m, "{class_decl.name.native}")'
  yield definition

  for s in _generate_constructors(class_decl):
    yield I + I + s

  for s in _generate_const_members(class_decl):
    yield I + I + s

  for s in _generate_methods(class_decl):
    yield I + I + s

  for s in _generate_variables(class_decl):
    yield I + I + s

  yield ';'


def _generate_constructors(class_decl: ast_pb2.ClassDecl):
  """Generates constructor methods."""
  for member in class_decl.members:
    if member.decltype == ast_pb2.Decl.Type.FUNC and member.func.name.native == '__init__':
      init_fn = '.def(py::init<'
      params = member.func.params
      for i, param in enumerate(params):
        init_fn += f'{param.type.lang_type}'
        if i != len(params) - 1:
          init_fn += ', '
      init_fn += '>())'
      yield init_fn

    elif member.decltype == ast_pb2.Decl.Type.FUNC and member.func.constructor:
      fn = f'.def_static("{member.func.name.native}", []('
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
      fn += '); })'
      yield fn


def _generate_const_members(class_decl: ast_pb2.ClassDecl):
  """Generates const member functions."""
  for member in class_decl.members:
    if member.decltype == ast_pb2.Decl.Type.CONST:
      yield (f'.def_readonly_static("{member.const.name.native}", '
             f'&{member.const.name.cpp_name})')


def _generate_methods(class_decl: ast_pb2.ClassDecl):
  """Generates methods."""
  for member in class_decl.members:
    if member.decltype == ast_pb2.Decl.Type.FUNC:
      if member.func.classmethod:
        yield (f'.def_static("{member.func.name.native}", '
               f'&{member.func.name.cpp_name})')
      elif not member.func.constructor:
        yield (f'.def("{member.func.name.native}", '
               f'&{member.func.name.cpp_name})')


def _generate_variables(class_decl: ast_pb2.ClassDecl):
  """Generates variables."""
  for member in class_decl.members:
    if member.decltype == ast_pb2.Decl.Type.VAR:
      # check if it is a var or property
      if member.var.HasField('cpp_get'):
        if member.var.HasField('cpp_set'):
          yield (f'.def_property("{member.var.name.native}", '
                 f'&{member.var.cpp_get.name.cpp_name}, '
                 f'&{member.var.cpp_set.name.cpp_name})')
        else:
          yield (f'.def_property_readonly("{member.var.name.native}", '
                 f'&{member.var.cpp_get.name.cpp_name})')
      else:
        yield (f'.def_readwrite("{member.var.name.native}", '
               f'&{class_decl.name.cpp_name}::{member.var.name.cpp_name})')
