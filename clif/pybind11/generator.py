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

from typing import Dict, Generator, Text, Set

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

  def generate_header(self,
                      unused_ast: ast_pb2.AST) -> Generator[Text, None, None]:
    # TODO: Generates header file content here.
    yield ''

  def generate_from(self, ast: ast_pb2.AST):
    """Generates pybind11 bindings code from CLIF ast.

    Args:
      ast: CLIF ast protobuf.

    Yields:
      Generated pybind11 bindings code.
    """
    yield from self._generate_headlines()

    # Find and keep track of virtual functions.
    python_override_class_names = {}
    # Every unique class requires a pybind11 smart holder type cast macro.
    unique_classes = set()

    for decl in ast.decls:
      yield from self._generate_python_override_class_names(
          python_override_class_names, decl)
      self._collect_class_cpp_names(decl, unique_classes)

    for c in unique_classes:
      yield f'PYBIND11_SMART_HOLDER_TYPE_CASTERS({c})'
    yield '\n'
    yield f'PYBIND11_MODULE({self._module_name}, m) {{'
    yield I+('m.doc() = "CLIF generated pybind11-based module for '
             f'{ast.source}";')

    for decl in ast.decls:
      if decl.decltype == ast_pb2.Decl.Type.FUNC:
        yield from function.generate_from('m', decl.func, None)
      elif decl.decltype == ast_pb2.Decl.Type.CONST:
        yield from self._generate_const_variables(decl.const)
      elif decl.decltype == ast_pb2.Decl.Type.CLASS:
        yield from classes.generate_from(
            decl.class_, 'm',
            python_override_class_names.get(decl.class_.name.cpp_name, ''))
      elif decl.decltype == ast_pb2.Decl.Type.ENUM:
        yield from enums.generate_from(decl.enum, 'm')
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
      if include:
        yield f'#include "{include}"'
    yield '#include "third_party/pybind11/include/pybind11/smart_holder.h"'
    yield '// potential future optimization: generate this line only as needed.'
    yield '#include "third_party/pybind11/include/pybind11/stl.h"'
    yield '#include <pybind11/operators.h>'
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

  def _generate_python_override_class_names(
      self, python_override_class_names: Dict[Text, Text], decl: ast_pb2.Decl):
    """Generates Python overrides classes dictionary for virtual functions."""
    if decl.decltype == ast_pb2.Decl.Type.CLASS:
      for member in decl.class_.members:
        if member.decltype == ast_pb2.Decl.Type.FUNC and member.func.virtual:
          assert decl.class_.name.cpp_name not in python_override_class_names
          python_override_class_name = f'{decl.class_.name.native}_vf'
          python_override_class_names[
              decl.class_.name.cpp_name] = python_override_class_name
          yield from self._generate_virtual_function(python_override_class_name,
                                                     decl.class_, member)

  def _generate_virtual_function(self, python_override_class_name: str,
                                 class_decl: ast_pb2.ClassDecl,
                                 member: ast_pb2.Decl):
    """Generates virtual functions."""
    yield (f'class {python_override_class_name} : public '
           f'{class_decl.name.cpp_name} {{')
    yield I + 'public:'
    yield I + I + f'using {class_decl.name.cpp_name}::{class_decl.name.native};'

    return_type = ''
    if member.func.cpp_void_return:
      return_type = 'void'
    elif member.func.returns:
      for v in member.func.returns:
        if v.HasField('cpp_exact_type'):
          return_type = v.cpp_exact_type

    params_list = []
    params_list_with_types = []
    for param in member.func.params:
      params_list.append(param.name.native)
      params_list_with_types.append(
          f'{param.type.lang_type} {param.name.native}')
    params_str = ', '.join(params_list)
    params_str_with_types = ', '.join(params_list_with_types)

    cpp_const = ''
    if member.func.cpp_const_method:
      cpp_const = ' const '

    yield I + I + (f'{return_type} '
                   f'{member.func.name.native}({params_str_with_types}) '
                   f'{cpp_const}override {{')

    if member.func.is_pure_virtual:
      pybind11_override = 'PYBIND11_OVERRIDE_PURE'
    else:
      pybind11_override = 'PYBIND11_OVERRIDE'

    yield I + I + I + f'{pybind11_override}('
    yield I + I + I + I + f'{return_type},'
    yield I + I + I + I + f'{class_decl.name.native},'
    yield I + I + I + I + f'{member.func.name.native},'
    yield I + I + I + I + f'{params_str}'
    yield I + I + I + ');'
    yield I + I + '}'
    yield '};'

  def _collect_class_cpp_names(self, decl: ast_pb2.Decl,
                               unique_classes: Set[Text]):
    """Traverses the AST and adds every class name to a set."""
    if decl.decltype == ast_pb2.Decl.Type.CLASS:
      unique_classes.add(decl.class_.name.cpp_name)
      for member in decl.class_.members:
        self._collect_class_cpp_names(member, unique_classes)


def write_to(channel, lines):
  """Writes the generated code to files."""
  for s in lines:
    channel.write(s)
    channel.write('\n')
