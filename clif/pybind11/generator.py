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
import types
from typing import Generator, List, Set

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


# Do a SWIG-like name mangling.
def _generate_mangled_name_for_module(full_dotted_module_name: str) -> str:
  """Converts `third_party.py.module` to `third__party_py_module`."""
  return full_dotted_module_name.replace('_', '__').replace('.', '_')


class ModuleGenerator(object):
  """A class that generates pybind11 bindings code from CLIF ast."""

  def __init__(self, ast: ast_pb2.AST, module_path: str, header_path: str,
               include_paths: List[str], pybind11_only_includes: List[str]):
    self._ast = ast
    self._module_path = module_path
    self._module_name = module_path.split('.')[-1]
    self._header_path = header_path
    self._include_paths = include_paths
    self._types = []
    self._capsule_types = set()
    self._namemap = {}
    self._registered_types = set()
    self._requires_status = False
    self._pybind11_only_includes = pybind11_only_includes

  def preprocess_ast(self) -> None:
    """Preprocess the ast to collect type information."""
    self._namemap = {
        m.name: types.SimpleNamespace(fq_name=m.fq_name, cpp_name='')
        for m in self._ast.namemaps
    }
    for decl in self._ast.decls:
      self._register_types(decl)
    self._types = sorted(self._types, key=lambda gen_type: gen_type.cpp_name)
    self._capsule_types = set([
        t.py_name for t in self._types
        if isinstance(t, gen_type_info.CapsuleType)
    ])
    cpp_import_types = type_casters.get_cpp_import_types(
        self._ast, self._include_paths)
    self._requires_status = 'absl::Status' in cpp_import_types
    python_import_types = set(
        [t.cpp_name for t in self._namemap.values() if t.cpp_name])
    self._registered_types = set([t.cpp_name for t in self._types]).union(
        cpp_import_types).union(python_import_types)

  def generate_header(self,
                      ast: ast_pb2.AST) -> Generator[str, None, None]:
    """Generates pybind11 bindings code from CLIF ast."""
    includes = set()
    for decl in ast.decls:
      includes.add(decl.cpp_file)
    yield '#include "third_party/pybind11/include/pybind11/smart_holder.h"'
    yield '#include "clif/python/postconv.h"'
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
    yield ''
    for m in ast.macros:
      macro_body = m.definition.decode('utf-8').replace('\n', r'\n')
      yield ''
      yield f'// CLIF macro {m.name} {macro_body}'

  def generate_from(self, ast: ast_pb2.AST):
    """Generates pybind11 bindings code from CLIF ast.

    Args:
      ast: CLIF ast protobuf.

    Yields:
      Generated pybind11 bindings code.
    """
    yield from self._generate_headlines()

    # Find and keep track of virtual functions.
    trampoline_class_names = set()

    for decl in ast.decls:
      yield from self._generate_trampoline_classes(trampoline_class_names, decl)
    yield ''
    yield from type_casters.generate_from(ast, self._include_paths)

    mangled_module_name = _generate_mangled_name_for_module(
        self._module_path)
    yield (f'GOOGLE_PYBIND11_MODULE({self._module_name}, '
           f'{mangled_module_name}, m) {{')
    yield from self._generate_import_modules(ast)
    yield I+('m.doc() = "CLIF-generated pybind11-based module for '
             f'{ast.source}";')
    if self._requires_status:
      yield I + 'py::google::ImportStatusModule();'
      yield I + 'py::google::PatchStatusBindings();'
    yield I + 'pybind11_protobuf::ImportNativeProtoCasters();'

    for decl in ast.decls:
      if decl.decltype == ast_pb2.Decl.Type.FUNC:
        for s in function.generate_from(
            'm', decl.func, self._capsule_types, None, self._requires_status):
          yield I + s
      elif decl.decltype == ast_pb2.Decl.Type.CONST:
        yield from consts.generate_from('m', decl.const)
      elif decl.decltype == ast_pb2.Decl.Type.CLASS:
        yield from classes.generate_from(
            decl.class_, 'm', trampoline_class_names, self._capsule_types,
            self._registered_types, self._requires_status)
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
    all_modules = set()
    for init in ast.extra_init:
      res = re.search(_IMPORTMODULEPATTERN, init)
      if res:
        all_modules.add(res.group('module_path'))
    for c in self._types:
      if isinstance(c, gen_type_info.ClassType):
        for b in c.py_bases:
          if b in self._namemap:
            fq_py_base = self._namemap[b].fq_name
            # converts `module.type` to `module`
            all_modules.add(fq_py_base[:fq_py_base.rfind('.')])
    for module_path in all_modules:
      yield I + f'py::module_::import("{module_path}");'

  def _generate_headlines(self):
    """Generates #includes and headers."""
    includes = set()
    for decl in self._ast.decls:
      includes.add(decl.cpp_file)
    for include in self._ast.usertype_includes:
      includes.add(include)
    for include in self._pybind11_only_includes:
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

    yield '// See pybind11_protobuf/proto_caster_impl.h'
    yield '#define PYBIND11_PROTOBUF_UNSAFE 1'
    yield '#include "third_party/pybind11_protobuf/native_proto_caster.h"'
    yield ''
    for include in includes:
      yield f'#include "{include}"'
    yield f'#include "{self._header_path}"'
    yield ''
    yield 'namespace py = pybind11;'
    yield ''

  def _generate_trampoline_classes(
      self, trampoline_class_names: Set[str], decl: ast_pb2.Decl):
    """Generates Python overrides classes dictionary for virtual functions."""
    if decl.decltype == ast_pb2.Decl.Type.CLASS:
      virtual_members = []
      for member in decl.class_.members:
        if member.decltype == ast_pb2.Decl.Type.FUNC and member.func.virtual:
          virtual_members.append(member)
      if not virtual_members:
        return
      trampoline_class_name = utils.trampoline_name(decl.class_)
      assert decl.class_.name.cpp_name not in trampoline_class_names
      trampoline_class_names.add(trampoline_class_name)
      yield (f'struct {trampoline_class_name} : {decl.class_.name.cpp_name}, '
             'py::trampoline_self_life_support {')
      class_name = decl.class_.name.cpp_name.split('::')[-1]
      yield I + f'using {decl.class_.name.cpp_name}::{class_name};'
      for member in virtual_members:
        yield from self._generate_virtual_function(
            decl.class_.name.native, member.func)
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

    # Characters like ',' may cause the `PYBIND11_OVERRIDE` macro parsing fail
    if ',' in return_type:
      yield I + I + f'using {func_decl.name.native}_return = {return_type};'
      return_type = f'{func_decl.name.native}_return'
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
      override_in_python = any(
          member.decltype == ast_pb2.Decl.Type.FUNC and member.func.virtual
          for member in decl.class_.members)
      py_name = decl.class_.name.native
      if parent_py_name:
        py_name = '.'.join([parent_py_name, py_name])
      py_bases = set(
          [b.native for b in decl.class_.bases if b.native and not b.cpp_name])
      class_type = gen_type_info.ClassType(
          cpp_name=decl.class_.name.cpp_name, py_name=py_name,
          cpp_namespace=cpp_namespace, py_bases=py_bases,
          cpp_has_public_dtor=decl.class_.cpp_has_public_dtor,
          cpp_copyable=(decl.class_.cpp_copyable and
                        not decl.class_.cpp_abstract),
          cpp_movable=(decl.class_.cpp_movable and
                       not decl.class_.cpp_abstract),
          override_in_python=override_in_python)
      self._types.append(class_type)
      if not decl.class_.suppress_upcasts:
        # TODO: Find a stable way to find cpp_name of the imported
        # base class. See b/225961086#comment22 for details.
        base_class_python_name = ''
        base_class_cpp_name = ''
        for i, base in enumerate(decl.class_.bases):
          if base.native and not base.cpp_name and base.native in self._namemap:
            base_class_python_name = base.native
            assert i + 1 < len(decl.class_.bases), (
                f'Cannot find cpp name for class "{base.native}"')
            assert decl.class_.bases[i+1].cpp_name, (
                f'Unexpected base class {decl.class_.bases[i+1]}')
            base_class_cpp_name = decl.class_.bases[i + 1].cpp_name
            break
        if base_class_python_name:
          for base in decl.class_.cpp_bases:
            class_cpp_name = base.name.split('::')[-1]
            if class_cpp_name == base_class_python_name:
              base_class_cpp_name = base.name
              break
          self._namemap[base_class_python_name].cpp_name = base_class_cpp_name
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
