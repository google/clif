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
from clif.pybind11 import function_lib
from clif.pybind11 import utils

I = utils.I


class ModuleGenerator(object):
  """A class that generates pybind11 bindings code from CLIF ast."""

  def __init__(self, ast: ast_pb2.AST, module_name: str):
    self._ast = ast
    self._module_name = module_name

  def generate_header(self,
                      unused_ast: ast_pb2.AST) -> Generator[str, None, None]:
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
    yield I+('m.doc() = "CLIF-generated pybind11-based module for '
             f'{ast.source}";')

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

  def _generate_headlines(self):
    """Generates #includes and headers."""
    includes = set()
    for decl in self._ast.decls:
      includes.add(decl.cpp_file)
      if decl.decltype == ast_pb2.Decl.Type.CONST:
        self._generate_const_variables_headers(decl.const, includes)
    yield '#include "third_party/pybind11/include/pybind11/complex.h"'
    yield '#include "third_party/pybind11/include/pybind11/functional.h"'
    yield '#include "third_party/pybind11/include/pybind11/operators.h"'
    yield '#include "third_party/pybind11/include/pybind11/smart_holder.h"'
    yield '// potential future optimization: generate this line only as needed.'
    yield '#include "third_party/pybind11/include/pybind11/stl.h"'
    for include in includes:
      if include:
        yield f'#include "{include}"'
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
          f'{function_lib.generate_param_type(p)} {p.name.cpp_name}')
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

  def _collect_class_cpp_names(self, decl: ast_pb2.Decl,
                               unique_classes: Set[Text]):
    """Adds every class name to a set. Only to be used in this context."""
    if decl.decltype == ast_pb2.Decl.Type.CLASS:
      unique_classes.add(decl.class_.name.cpp_name)
      for member in decl.class_.members:
        self._collect_class_cpp_names(member, unique_classes)


def write_to(channel, lines):
  """Writes the generated code to files."""
  for s in lines:
    channel.write(s)
    channel.write('\n')
