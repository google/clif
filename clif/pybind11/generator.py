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

import itertools
import re
from typing import Dict, Generator, List, Text

from clif.protos import ast_pb2
from clif.pybind11 import classes
from clif.pybind11 import consts
from clif.pybind11 import enums
from clif.pybind11 import function
from clif.pybind11 import gen_type_info
from clif.pybind11 import type_casters
from clif.pybind11 import utils

I = utils.I

_IMPORTMODULEPATTERN = r'module_path:(?P<module_path>.*)'


class ModuleGenerator(object):
  """A class that generates pybind11 bindings code from CLIF ast."""

  def __init__(self, ast: ast_pb2.AST, module_path: str, header_path: str,
               include_paths: List[str]):
    self._ast = ast
    self._module_path = module_path
    self._module_name = module_path.split('.')[-1]
    self._header_path = header_path
    self._include_paths = include_paths
    self._types = []
    self._capsule_types = set()
    self._all_types = set()

  def register_types(self, ast: ast_pb2.AST) -> None:
    """Preprocess the ast to collect type information."""
    for decl in ast.decls:
      self._register_types(decl)
    self._types = sorted(self._types, key=lambda gen_type: gen_type.cpp_name)
    self._capsule_types = set([
        t.py_name for t in self._types
        if isinstance(t, gen_type_info.CapsuleType)
    ])

  def generate_header(self,
                      ast: ast_pb2.AST) -> Generator[str, None, None]:
    """Generates pybind11 bindings code from CLIF ast."""
    includes = set()
    for decl in ast.decls:
      includes.add(decl.cpp_file)
    yield '#include "third_party/pybind11/include/pybind11/smart_holder.h"'
    for include in includes:
      yield f'#include "{include}"'
    yield ''
    for typedef in self._types:
      yield from typedef.generate_type_caster()
    yield ''

    for namespace, typedefs in itertools.groupby(
        self._types, lambda gen_type: gen_type.cpp_namespace):
      namespace = namespace.strip(':') or 'clif'
      yield ' '.join('namespace %s {' % ns for ns in namespace.split('::'))
      for t in typedefs:
        yield from t.generate_header()
      yield '} ' * (1 + namespace.count('::')) + ' // namespace ' + namespace
    yield ''
    yield f'// CLIF init_module module_path:{self._module_path}'

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

    imported_types = type_casters.get_imported_types(ast, self._include_paths)
    known_types = set([t.cpp_name for t in self._types])
    unknown_types = self._all_types.difference(imported_types).difference(
        known_types)
    for unknown_type in unknown_types:
      yield f'PYBIND11_SMART_HOLDER_TYPE_CASTERS({unknown_type})'

    yield from type_casters.generate_from(ast, self._include_paths)
    yield f'PYBIND11_MODULE({self._module_name}, m) {{'
    yield from self._generate_import_modules(ast)
    yield I+('m.doc() = "CLIF-generated pybind11-based module for '
             f'{ast.source}";')
    yield I + 'py::google::ImportStatusModule();'
    for i, unknown_type in enumerate(unknown_types):
      yield I + '{'
      yield I + I+ f'py::classh<{unknown_type}> CLIFBase{i}(m, "CLIFBase{i}");'
      yield I + '}'

    for decl in ast.decls:
      if decl.decltype == ast_pb2.Decl.Type.FUNC:
        for s in function.generate_from(
            'm', decl.func, self._capsule_types, None):
          yield I + s
      elif decl.decltype == ast_pb2.Decl.Type.CONST:
        yield from consts.generate_from('m', decl.const)
      elif decl.decltype == ast_pb2.Decl.Type.CLASS:
        yield from classes.generate_from(
            decl.class_, 'm',
            python_override_class_names.get(decl.class_.name.cpp_name, ''),
            self._capsule_types)
      elif decl.decltype == ast_pb2.Decl.Type.ENUM:
        yield from enums.generate_from('m', decl.enum)
    yield '}'
    yield ''
    for namespace, typedefs in itertools.groupby(
        self._types, lambda gen_type: gen_type.cpp_namespace):
      namespace = namespace.strip(':') or 'clif'
      yield ' '.join('namespace %s {' % ns for ns in namespace.split('::'))
      for t in typedefs:
        yield from t.generate_converters()
      yield '} ' * (1 + namespace.count('::')) + ' // namespace ' + namespace

  def _generate_import_modules(self,
                               ast: ast_pb2.AST) -> Generator[str, None, None]:
    """Generates pybind11 module imports."""
    for init in ast.extra_init:
      res = re.search(_IMPORTMODULEPATTERN, init)
      if res:
        module_path = res.group('module_path')
        yield I + f'py::module_::import("{module_path}");'

  def _generate_headlines(self):
    """Generates #includes and headers."""
    includes = set()
    for decl in self._ast.decls:
      includes.add(decl.cpp_file)
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

  def _register_types(self, decl: ast_pb2.Decl, parent_py_name: str = '',
                      cpp_namespace: str = '') -> None:
    """Register classes and enums defined in the ast."""
    cpp_namespace = decl.namespace_ if decl.namespace_ else cpp_namespace
    if decl.decltype == ast_pb2.Decl.Type.CLASS:
      py_name = decl.class_.name.native
      if parent_py_name:
        py_name = '.'.join([parent_py_name, py_name])
      class_type = gen_type_info.ClassType(
          cpp_name=decl.class_.name.cpp_name, py_name=py_name,
          cpp_namespace=cpp_namespace)
      self._types.append(class_type)
      if not decl.class_.suppress_upcasts:
        bases = list(decl.class_.bases)
        i = 0
        while i < len(bases):
          base = bases[i]
          # Note: We are using a hack to avoid redefining aliased types. When
          # a class inherits another class that is already defined in the .clif
          # file, it is possible that base.cpp_name is an aliased name.
          # Therefore we might generate duplicated wrapper code for the same
          # class.
          if base.native and not base.cpp_name:
            # The class inherits from another class defined in .clif file. Two
            # base definitions whose indexes are consecutive exist in the ast
            # that refers to the same class.
            assert i + 1 < len(bases), ('Cannot find cpp name for class '
                                        f'{base.native}')
            assert bases[i+1].cpp_name, f'Unexpected base class {bases[i+1]}'
            i += 2
          else:
            if base.cpp_name:
              self._all_types.add(base.cpp_name)
            i += 1
      for member in decl.class_.members:
        self._register_types(member, py_name, cpp_namespace)
    elif decl.decltype == ast_pb2.Decl.Type.ENUM:
      py_name = decl.enum.name.native
      if parent_py_name:
        py_name = '.'.join([parent_py_name, py_name])
      enum_type = gen_type_info.EnumType(
          cpp_name=decl.enum.name.cpp_name, py_name=py_name,
          cpp_namespace=cpp_namespace)
      self._types.append(enum_type)
    elif decl.decltype == ast_pb2.Decl.Type.TYPE:
      py_name = decl.fdecl.name.native
      if parent_py_name:
        py_name = '.'.join([parent_py_name, py_name])
      capsule_type = gen_type_info.CapsuleType(
          cpp_name=decl.fdecl.name.cpp_name, py_name=py_name,
          cpp_namespace=cpp_namespace)
      self._types.append(capsule_type)


def write_to(channel, lines):
  """Writes the generated code to files."""
  for s in lines:
    channel.write(s)
    channel.write('\n')
