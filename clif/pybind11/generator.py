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
      yield ''
    yield '}'

  def _generate_headlines(self):
    """Generates #includes and headers."""
    includes = set()
    for decl in self._ast.decls:
      includes.add(decl.cpp_file)
    for include in includes:
      yield f'#include "{include}"'
    yield '#include "third_party/pybind11/include/pybind11/pybind11.h"'
    yield ''
    yield 'namespace py = pybind11;'
    yield ''


def write_to(channel, lines):
  """Writes the generated code to files."""
  for s in lines:
    channel.write(s)
    channel.write('\n')
