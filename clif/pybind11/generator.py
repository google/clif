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

from typing import Dict, Generator, List, Text, Set

from clif.protos import ast_pb2
from clif.pybind11 import classes
from clif.pybind11 import enums
from clif.pybind11 import function
from clif.pybind11 import type_casters
from clif.pybind11 import utils

I = utils.I


class ModuleGenerator(object):
  """A class that generates pybind11 bindings code from CLIF ast."""

  def __init__(self, ast: ast_pb2.AST, module_name: str, header_path: str,
               include_paths: List[str]):
    self._ast = ast
    self._module_name = module_name
    self._header_path = header_path
    self._include_paths = include_paths
    self._unique_classes = {}
    self._unique_enums = {}

  def generate_header(self,
                      ast: ast_pb2.AST) -> Generator[str, None, None]:
    """Generates pybind11 bindings code from CLIF ast."""
    includes = set()
    for decl in ast.decls:
      includes.add(decl.cpp_file)
      self._collect_cpp_names_to_export(decl)
    yield '#include "third_party/pybind11/include/pybind11/smart_holder.h"'
    for include in includes:
      yield f'#include "{include}"'
    yield '\n'
    for cpp_name in self._unique_classes:
      yield f'PYBIND11_SMART_HOLDER_TYPE_CASTERS({cpp_name})'
    yield '\n'
    for cpp_name, py_name in self._unique_classes.items():
      yield f'// CLIF use `{cpp_name}` as {py_name}'
    for cpp_name, py_name in self._unique_enums.items():
      yield f'// CLIF use `{cpp_name}` as {py_name}'

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

    for decl in ast.decls:
      yield from self._generate_python_override_class_names(
          python_override_class_names, decl)
      self._collect_cpp_names_to_export(decl)

    yield from type_casters.generate_from(ast, self._include_paths)
    yield f'PYBIND11_MODULE({self._module_name}, m) {{'
    yield from self._generate_import_modules(ast)
    yield I+('m.doc() = "CLIF-generated pybind11-based module for '
             f'{ast.source}";')
    yield I + 'py::google::ImportStatusModule();'

    for decl in ast.decls:
      if decl.decltype == ast_pb2.Decl.Type.FUNC:
        for s in function.generate_from('m', decl.func, None):
          yield I + s
      elif decl.decltype == ast_pb2.Decl.Type.CONST:
        yield from self._generate_const_variables(decl.const)
      elif decl.decltype == ast_pb2.Decl.Type.CLASS:
        yield from classes.generate_from(
            decl.class_, 'm',
            python_override_class_names.get(decl.class_.name.cpp_name, ''))
      elif decl.decltype == ast_pb2.Decl.Type.ENUM:
        yield from enums.generate_from('m', decl.enum)
      yield ''
    yield '}'

  def _generate_import_modules(self,
                               ast: ast_pb2.AST) -> Generator[str, None, None]:
    for include in ast.pybind11_includes:
      # Converts `full/project/path/cheader_pybind11_clif.h` to
      # `full.project.path.cheader_pybind11`
      names = include.split('/')
      names.insert(0, 'google3')
      names[-1] = names[-1][:-len('_clif.h')]
      module = '.'.join(names)
      yield f'py::module_::import("{module}");'

  def _generate_headlines(self):
    """Generates #includes and headers."""
    includes = set()
    for decl in self._ast.decls:
      includes.add(decl.cpp_file)
      if decl.decltype == ast_pb2.Decl.Type.CONST:
        self._generate_const_variables_headers(decl.const, includes)
    for include in self._ast.pybind11_includes:
      includes.add(include)
    for include in self._ast.usertype_includes:
      includes.add(include)
    yield '#include "third_party/pybind11/include/pybind11/complex.h"'
    yield '#include "third_party/pybind11/include/pybind11/functional.h"'
    yield '#include "third_party/pybind11/include/pybind11/operators.h"'
    yield '#include "third_party/pybind11/include/pybind11/smart_holder.h"'
    yield '// potential future optimization: generate this line only as needed.'
    yield '#include "third_party/pybind11/include/pybind11/stl.h"'
    yield ''
    yield '#include "clif/pybind11/runtime.h"'
    yield '#include "clif/pybind11/type_casters.h"'
    yield ''
    for include in includes:
      yield f'#include "{include}"'
    yield f'#include "{self._header_path}"'
    yield ''
    yield 'namespace py = pybind11;'
    yield ''

  def _generate_const_variables_headers(self, const_decl: ast_pb2.ConstDecl,
                                        includes: Set[str]):
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
      self, python_override_class_names: Dict[Text, Text], decl: ast_pb2.Decl,
      trampoline_name_suffix: str = '_trampoline',
      self_life_support: str = 'py::trampoline_self_life_support'):
    """Generates Python overrides classes dictionary for virtual functions."""
    if decl.decltype == ast_pb2.Decl.Type.CLASS:
      virtual_members = []
      for member in decl.class_.members:
        if member.decltype == ast_pb2.Decl.Type.FUNC and member.func.virtual:
          virtual_members.append(member)
      if not virtual_members:
        return
      python_override_class_name = (
          f'{decl.class_.name.native}_{trampoline_name_suffix}')
      assert decl.class_.name.cpp_name not in python_override_class_names
      python_override_class_names[
          decl.class_.name.cpp_name] = python_override_class_name
      yield (f'struct {python_override_class_name} : '
             f'{decl.class_.name.cpp_name}, {self_life_support} {{')
      yield I + (
          f'using {decl.class_.name.cpp_name}::{decl.class_.name.native};')
      for member in virtual_members:
        yield from self._generate_virtual_function(
            decl.class_.name.native, member.func)
      if python_override_class_name:
        yield '};'

  def _generate_virtual_function(self,
                                 class_name: str, func_decl: ast_pb2.FuncDecl):
    """Generates virtual function overrides calling Python methods."""
    return_type = ''
    if func_decl.cpp_void_return:
      return_type = 'void'
    elif func_decl.returns:
      for v in func_decl.returns:
        if v.HasField('cpp_exact_type'):
          return_type = v.cpp_exact_type

    params = ', '.join([f'{p.name.cpp_name}' for p in func_decl.params])
    params_list_with_types = []
    for p in func_decl.params:
      params_list_with_types.append(
          f'{p.cpp_exact_type} {p.name.cpp_name}')
    params_str_with_types = ', '.join(params_list_with_types)

    cpp_const = ''
    if func_decl.cpp_const_method:
      cpp_const = ' const'

    yield I + (f'{return_type} '
               f'{func_decl.name.native}({params_str_with_types}) '
               f'{cpp_const} override {{')

    if func_decl.is_pure_virtual:
      pybind11_override = 'PYBIND11_OVERRIDE_PURE'
    else:
      pybind11_override = 'PYBIND11_OVERRIDE'

    yield I + I + f'{pybind11_override}('
    yield I + I + I + f'{return_type},'
    yield I + I + I + f'{class_name},'
    yield I + I + I + f'{func_decl.name.native},'
    yield I + I + I + f'{params}'
    yield I + I + ');'
    yield I + '}'

  def _collect_cpp_names_to_export(self, decl: ast_pb2.Decl,
                                   parent_name: str = '') -> None:
    """Adds every class and enum name to a set."""
    if decl.decltype == ast_pb2.Decl.Type.CLASS:
      full_native_name = decl.class_.name.native
      if parent_name:
        full_native_name = '.'.join([parent_name, full_native_name])
      self._unique_classes[decl.class_.name.cpp_name] = full_native_name
      for member in decl.class_.members:
        self._collect_cpp_names_to_export(member, full_native_name)
    elif decl.decltype == ast_pb2.Decl.Type.ENUM:
      full_native_name = decl.enum.name.native
      full_cpp_name = decl.enum.name.cpp_name
      if parent_name:
        full_native_name = '.'.join([parent_name, full_native_name])
      self._unique_enums[full_cpp_name] = full_native_name


def write_to(channel, lines):
  """Writes the generated code to files."""
  for s in lines:
    channel.write(s)
    channel.write('\n')
