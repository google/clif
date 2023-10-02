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
from typing import Generator, List, Set

from clif.protos import ast_pb2
from clif.pybind11 import classes
from clif.pybind11 import consts
from clif.pybind11 import enums
from clif.pybind11 import function
from clif.pybind11 import function_lib
from clif.pybind11 import gen_type_info
from clif.pybind11 import topo_sort
from clif.pybind11 import type_casters
from clif.pybind11 import utils

I = utils.I

_IMPORTMODULEPATTERN = r'module_path:(?P<module_path>.*)'

CLIF_MATCHER_VERSION_STAMP_REQUIRED_MINIMUM = 531560963


class ModuleGenerator:
  """A class that generates pybind11 bindings code from CLIF ast."""

  def __init__(self, ast: ast_pb2.AST, module_path: str, header_path: str,
               include_paths: List[str], pybind11_only_includes: List[str]):
    self._ast = ast
    self._module_path = module_path
    self._module_name = module_path.split('.')[-1]
    self._header_path = header_path
    self._include_paths = include_paths
    self._types = []
    self._extend_from_python = ast.options.get(
        'is_extended_from_python', 'False') == 'True'
    self._pybind11_only_includes = pybind11_only_includes
    self._codegen_info = None

  def preprocess_ast(self) -> None:
    """Preprocess the ast to collect type information."""
    topo_sort.topo_sort_ast_in_place(self._ast)
    namemap = {
        m.name: m.fq_name
        for m in self._ast.namemaps
    }
    for decl in self._ast.decls:
      self._register_types(decl)
    self._types = sorted(self._types, key=lambda gen_type: gen_type.cpp_name)
    cpp_import_types = type_casters.get_cpp_import_types(
        self._ast, self._include_paths)
    imported_capsule_types = set([
        t.py_name for t in cpp_import_types
        if t.python_capsule
    ])
    capsule_types = set([
        t.py_name for t in self._types
        if isinstance(t, gen_type_info.CapsuleType)
    ]).union(imported_capsule_types)
    dynamic_attr_types = set([
        t.cpp_name for t in self._types
        if isinstance(t, gen_type_info.ClassType) and t.enable_instance_dict
    ])
    cpp_import_type_cpp_names = set([t.cpp_name for t in cpp_import_types])
    requires_status = 'absl::Status' in cpp_import_type_cpp_names
    self._codegen_info = utils.CodeGenInfo(
        capsule_types=capsule_types, requires_status=requires_status,
        namemap=namemap, dynamic_attr_types=dynamic_attr_types)

  def generate_pyinit(self) -> Generator[str, None, None]:
    yield '#include <Python.h>'
    yield ''
    mangled_module_name = utils.generate_mangled_name_for_module(
        self._module_path)
    yield f'extern "C" PyObject* GooglePyInit_{mangled_module_name}();'
    yield ''
    yield f'extern "C" PyObject* PyInit_{self._module_name}() {{'
    yield I + f'return GooglePyInit_{mangled_module_name}();'
    yield '}'

  def generate_header(self,
                      ast: ast_pb2.AST) -> Generator[str, None, None]:
    """Generates pybind11 bindings code from CLIF ast."""
    includes = set()
    for decl in ast.decls:
      includes.add(decl.cpp_file)
    for include in self._ast.usertype_includes:
      includes.add(include)
    for include in self._pybind11_only_includes:
      includes.add(include)
    yield '#include "third_party/pybind11/include/pybind11/smart_holder.h"'
    yield '#include "clif/python/postconv.h"'
    for include in includes:
      yield f'#include "{include}"'
    yield ''
    yield '#if !defined(PYCLIF_CODE_GEN_PYBIND11)'
    yield I + '#define PYCLIF_CODE_GEN_PYBIND11'
    yield '#endif'
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

    module_path = self._module_path
    if self._extend_from_python:
      flds = module_path.split('.')
      if not flds[-1].startswith('_'):
        raise ValueError(
            'OPTION is_extended_from_python is applicable only to private'
            ' extensions (i.e. the unqualified name of the extension must'
            ' start with an underscore). Fully-qualified extension name: %s'
            % module_path)
      flds[-1] = flds[-1][1:]
      module_path = '.'.join(flds)
    yield ''
    yield f'// CLIF init_module module_path:{module_path}'
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

    Raises:
      RuntimeError: When the CLIF matcher we are using is out of date.
    """

    assert self._codegen_info is not None, '_codegen_info should be initialized'
    if (
        ast.clif_matcher_version_stamp is None
        or ast.clif_matcher_version_stamp
        < CLIF_MATCHER_VERSION_STAMP_REQUIRED_MINIMUM
    ):
      raise RuntimeError(
          'Incompatible clif_matcher_version_stamp'
          f' ("{ast.clif_matcher_argv0}"):'
          f' {ast.clif_matcher_version_stamp} (required minimum:'
          f' {CLIF_MATCHER_VERSION_STAMP_REQUIRED_MINIMUM})'
      )

    yield from self._generate_headlines()

    # Find and keep track of virtual functions.
    trampoline_class_names = set()

    for decl in ast.decls:
      yield from self._generate_trampoline_classes(trampoline_class_names, decl)
    yield ''
    yield from type_casters.generate_from(ast, self._include_paths)

    yield 'namespace {'
    yield ''
    yield 'PyObject * this_module_init() noexcept {'
    yield I + 'PYBIND11_CHECK_PYTHON_VERSION'
    yield I + 'PYBIND11_ENSURE_INTERNALS_READY'
    yield I + ('static pybind11::module_::module_def '
               f'module_def_{self._module_name};')
    yield I + ('auto m = pybind11::module_::create_extension_module('
               f'"{self._module_name}", nullptr, '
               f'&module_def_{self._module_name});')
    yield I + 'try {'
    for s in self._generate_import_modules(ast):
      yield I + s
    yield I + I + ('m.doc() = "CLIF-generated pybind11-based module for '
                   f'{ast.source}";')
    if self._codegen_info.requires_status:
      yield I + I + ('pybind11::module_::import('
                     '"util.task.python.error");')
    yield I + I + 'pybind11_protobuf::ImportNativeProtoCasters();'

    for decl in ast.decls:
      if decl.decltype == ast_pb2.Decl.Type.FUNC:
        for s in function.generate_from(
            'm', decl.func, self._codegen_info, None):
          yield I + I + s
      elif decl.decltype == ast_pb2.Decl.Type.CONST:
        for s in consts.generate_from('m', decl.const):
          yield I + s
      elif decl.decltype == ast_pb2.Decl.Type.CLASS:
        for s in classes.generate_from(
            decl, 'm', trampoline_class_names, self._codegen_info):
          yield I + s
      elif decl.decltype == ast_pb2.Decl.Type.ENUM:
        for s in enums.generate_from('m', decl.enum):
          yield I + s
    yield I + I + 'return m.ptr();'
    yield I + '}'
    yield I + 'PYBIND11_CATCH_INIT_EXCEPTIONS'
    yield '}'
    yield ''
    yield '}  // namespace'
    yield ''
    mangled_module_name = utils.generate_mangled_name_for_module(
        self._module_path)
    yield f'extern "C" PyObject* GooglePyInit_{mangled_module_name}() {{'
    yield I + 'return this_module_init();'
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
    assert self._codegen_info is not None, '_codegen_info should be initialized'
    for c in self._types:
      if isinstance(c, gen_type_info.ClassType):
        for b in c.py_bases:
          if b in self._codegen_info.namemap:
            fq_py_base = self._codegen_info.namemap[b]
            # converts `module.type` to `module`
            all_modules.add(fq_py_base[:fq_py_base.rfind('.')])
    for module_path in all_modules:
      module_variable_name = utils.generate_mangled_name_for_module(
          module_path)
      yield I + (f'auto {module_variable_name} = '
                 f'py::module_::import("{module_path}");')

  def _generate_headlines(self):
    """Generates #includes and headers."""
    includes = set()
    for include in self._ast.usertype_includes:
      includes.add(include)
    for include in self._pybind11_only_includes:
      includes.add(include)
    yield '#include "third_party/pybind11/include/pybind11/complex.h"'
    yield '#include "third_party/pybind11/include/pybind11/functional.h"'
    yield '#include "third_party/pybind11/include/pybind11/native_enum.h"'
    yield '#include "third_party/pybind11/include/pybind11/operators.h"'
    yield '#include "third_party/pybind11/include/pybind11/smart_holder.h"'
    yield '#include "third_party/pybind11/include/pybind11/stl.h"'
    yield '#include "third_party/pybind11/include/pybind11/type_caster_pyobject_ptr.h"'  # pylint: disable=long-line
    yield ''
    yield '// See pybind11_protobuf/proto_caster_impl.h'
    yield '#if !defined(PYBIND11_PROTOBUF_UNSAFE)'
    yield I + '#define PYBIND11_PROTOBUF_UNSAFE 1'
    yield '#endif'
    yield ''
    for include in includes:
      yield f'#include "{include}"'
    yield f'#include "{self._header_path}"'
    yield '#include "clif/pybind11/clif_type_casters.h"'
    yield '#include "clif/pybind11/runtime.h"'
    yield '#include "clif/pybind11/type_casters.h"'
    yield '#include "third_party/pybind11_protobuf/native_proto_caster.h"'
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
            decl.class_.name.cpp_name, member.func)
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

    params_list = []
    for p in func_decl.params:
      if p.type.lang_type == 'bytes' and 'std::string' in p.cpp_exact_type:
        params_list.append(f'py::bytes({p.name.cpp_name})')
      else:
        params_list.append(p.name.cpp_name)
    params = ', '.join(params_list)
    params_list_with_types = []
    for p in func_decl.params:
      params_list_with_types.append(
          f'{p.cpp_exact_type} {p.name.cpp_name}')
    params_str_with_types = ', '.join(params_list_with_types)

    cpp_const = ''
    if func_decl.cpp_const_method:
      cpp_const = ' const'

    function_name = func_decl.name.cpp_name.split('::')[-1]
    yield I + (f'{return_type} '
               f'{function_name}({params_str_with_types}) '
               f'{cpp_const} override {{')

    if func_decl.is_pure_virtual:
      if 'absl::StatusOr' in return_type:
        pybind11_override = 'PYBIND11_OVERRIDE_PURE_STATUSOR_RETURN'
      elif 'absl::Status' in return_type:
        pybind11_override = 'PYBIND11_OVERRIDE_PURE_STATUS_RETURN'
      else:
        pybind11_override = 'PYBIND11_OVERRIDE_PURE_NAME_RVPP'
    else:
      if 'absl::StatusOr' in return_type:
        pybind11_override = 'PYBIND11_OVERRIDE_STATUSOR_RETURN'
      elif 'absl::Status' in return_type:
        pybind11_override = 'PYBIND11_OVERRIDE_STATUS_RETURN'
      else:
        pybind11_override = 'PYBIND11_OVERRIDE_NAME_RVPP'

    # Characters like ',' may cause the `PYBIND11_OVERRIDE_NAME` macro parsing
    # fail
    if ',' in return_type:
      yield I + I + f'using {func_decl.name.native}_return = {return_type};'
      return_type = f'{func_decl.name.native}_return'
    yield I + I + 'py::gil_scoped_acquire hold_gil;'
    yield I + I + f'{pybind11_override}('
    if pybind11_override not in ('PYBIND11_OVERRIDE_STATUS_RETURN',
                                 'PYBIND11_OVERRIDE_PURE_STATUS_RETURN'):
      yield I + I + I + f'{return_type},'
    yield I + I + I + f'{class_name},'
    yield I + I + I + f'"{func_decl.name.native}",'
    yield I + I + I + f'{function_name},'
    return_value_policy = (
        function_lib.generate_return_value_policy_for_func_decl_params(
            func_decl
        )
    )
    return_value_policy_pack = (
        f'py::return_value_policy_pack({return_value_policy})'
    )
    if params:
      yield I + I + I + f'{return_value_policy_pack},'
      yield I + I + I + f'{params}'
    else:
      yield I + I + I + f'{return_value_policy_pack}'
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
          [b.native for b in decl.class_.bases if b.native and
           not b.cpp_canonical_type])
      class_type = gen_type_info.ClassType(
          cpp_name=decl.class_.name.cpp_canonical_type, py_name=py_name,
          cpp_namespace=cpp_namespace, py_bases=py_bases,
          cpp_has_public_dtor=decl.class_.cpp_has_public_dtor,
          cpp_copyable=(decl.class_.cpp_copyable and
                        not decl.class_.cpp_abstract),
          cpp_movable=(decl.class_.cpp_movable and
                       not decl.class_.cpp_abstract),
          override_in_python=override_in_python,
          enable_instance_dict=decl.class_.enable_instance_dict)
      self._types.append(class_type)
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
