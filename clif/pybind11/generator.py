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

"""Generates pybind11 bindings code."""

from typing import Text

from clif.protos import ast_pb2
from clif.pybind11 import classes
from clif.pybind11 import enums
from clif.pybind11 import function
from clif.pybind11 import utils

I = utils.I


class ModuleGenerator(object):
  """A class that generates pybind11 bindings code from CLIF ast."""

  def __init__(self, ast: ast_pb2.AST, module_name: Text):
    self._ast = ast
    self._module_name = module_name

  def generate_from(self, ast: ast_pb2.AST):
    """Generates pybind11 bindings code from CLIF ast.

    Args:
      ast: CLIF ast protobuf.

    Yields:
      Generated pybind11 bindings code.
    """
    for s in self._generate_headlines():
      yield s
    yield f'PYBIND11_MODULE({self._module_name}, m) {{'
    yield I+('m.doc() = "CLIF generated pybind11-based module for '
             f'{ast.source}";')
    for decl in ast.decls:
      if decl.decltype == ast_pb2.Decl.Type.FUNC:
        for s in function.generate_from(decl.func):
          yield s
      elif decl.decltype == ast_pb2.Decl.Type.CONST:
        for s in self._generate_const_variables(decl.const):
          yield s
      elif decl.decltype == ast_pb2.Decl.Type.CLASS:
        for s in classes.generate_from(decl.class_, 'm'):
          yield s
      elif decl.decltype == ast_pb2.Decl.Type.ENUM:
        for s in enums.generate_from(decl.enum, 'm'):
          yield s
      yield ''
    yield '}'

  def _generate_headlines(self):
    """Generates #includes and headers."""
    includes = set()
    for decl in self._ast.decls:
      includes.add(decl.cpp_file)
      if decl.decltype == ast_pb2.Decl.Type.CONST:
        self._generate_const_variables_headers(decl.const, includes)
    for include in includes:
      yield f'#include "{include}"'
    yield '#include "third_party/pybind11/include/pybind11/pybind11.h"'
    yield ''
    yield 'namespace py = pybind11;'
    yield ''

  def _generate_const_variables_headers(self, const_decl: ast_pb2.ConstDecl,
                                        includes: set):
    if const_decl.type.lang_type == 'complex':
      includes.add('third_party/pybind11/include/pybind11/complex.h')
    if (const_decl.type.lang_type.startswith('list<') or
        const_decl.type.lang_type.startswith('dict<') or
        const_decl.type.lang_type.startswith('set<')):
      includes.add('third_party/pybind11/include/pybind11/stl.h')

  def _generate_const_variables(self, const_decl: ast_pb2.ConstDecl):
    """Generates variables."""
    lang_type = const_decl.type.lang_type

    if (lang_type in {'int', 'float', 'double', 'bool', 'str'} or
        lang_type.startswith('tuple<')):
      const_def = I + (f'm.attr("{const_decl.name.native}") = '
                       f'{const_decl.name.cpp_name};')
    else:
      const_def = I + (f'm.attr("{const_decl.name.native}") = '
                       f'py::cast({const_decl.name.cpp_name});')

    yield const_def


def write_to(channel, lines):
  """Writes the generated code to files."""
  for s in lines:
    channel.write(s)
    channel.write('\n')
