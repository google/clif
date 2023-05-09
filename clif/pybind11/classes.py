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

from typing import Generator, Optional, Set

from clif.protos import ast_pb2
from clif.pybind11 import consts
from clif.pybind11 import enums
from clif.pybind11 import function
from clif.pybind11 import function_lib
from clif.pybind11 import utils
from clif.pybind11 import variables
from clif.python import clif_types as types as legacy_types

I = utils.I


def generate_from(
    decl: ast_pb2.Decl, superclass_name: str,
    trampoline_class_names: Set[str], codegen_info: utils.CodeGenInfo,
) -> Generator[str, None, None]:
  """Generates a complete py::class_<>.

  Args:
    decl: Class declaration in proto format.
    superclass_name: String name of the superclass.
    trampoline_class_names: A Set of class names whose member functions
      will be overriden in Python.
    codegen_info: The information needed to generate pybind11 code.

  Yields:
    pybind11 class bindings code.
  """
  class_decl = decl.class_
  yield I + '{'
  if decl.namespace_:
    namespaces = decl.namespace_.strip(':').split('::')
    for i in range(0, len(namespaces)):
      namespace = '::'.join(namespaces[:i + 1])
      yield I + I + f'using namespace {namespace};'
  class_name = f'{class_decl.name.native}_class'
  definition = f'py::classh<{class_decl.name.cpp_name}'
  implicit_upcast_bases = []
  if not class_decl.suppress_upcasts:
    for base in class_decl.bases:
      if base.HasField('cpp_canonical_type'):
        if base.cpp_canonical_type in codegen_info.registered_types:
          definition += f', {base.cpp_canonical_type}'
        else:
          implicit_upcast_bases.append(base)
  trampoline_class_name = utils.trampoline_name(class_decl)
  if trampoline_class_name in trampoline_class_names:
    definition += f', {trampoline_class_name}'
  definition += (f'> {class_name}({superclass_name}, '
                 f'"{class_decl.name.native}"')
  if class_decl.HasField('docstring'):
    definition += f', {function_lib.generate_docstring(class_decl.docstring)}'
  if class_decl.enable_instance_dict:
    definition += ', py::dynamic_attr()'
  if class_decl.final:
    definition += ', py::is_final()'
  definition += ');'
  yield I + I + definition

  ctor_defined = False
  reduce_or_reduce_ex_defined = False
  trampoline_generated = (
      utils.trampoline_name(class_decl) in trampoline_class_names)
  for member in class_decl.members:
    if member.decltype == ast_pb2.Decl.Type.CONST:
      for s in consts.generate_from(class_name, member.const):
        yield I + I + s
    elif member.decltype == ast_pb2.Decl.Type.FUNC:
      if member.func.name.native in ('__reduce__', '__reduce_ex__'):
        reduce_or_reduce_ex_defined = True
      if member.func.constructor:
        # Legacy CLIF ignores __init__ for abstract classes.
        # Potential future cleanup project: generate a user-friendly error
        # instead.
        if (not class_decl.cpp_abstract or trampoline_generated) and (
            class_decl.cpp_has_def_ctor or member.func.params):
          for s in _generate_constructor(class_name, member.func, class_decl,
                                         trampoline_generated, codegen_info):
            yield I + I + s
          if not ctor_defined:
            ctor_defined = member.func.name.native == '__init__'
      else:
        # This function will be overriden in Python. Do not call it from the
        # abstract base class.
        if class_decl.cpp_abstract and member.func.virtual:
          continue
        else:
          for s in function.generate_from(
              class_name, member.func, codegen_info, class_decl):
            yield I + I + s
          for s in function_lib.setstate_workaround_move_attr(
              class_name, member.func.name.native):
            yield I + I + s
    elif member.decltype == ast_pb2.Decl.Type.VAR:
      for s in variables.generate_from(class_name, member.var, class_decl):
        yield I + I + s
    elif member.decltype == ast_pb2.Decl.Type.ENUM:
      for s in enums.generate_from(class_name, member.enum):
        yield I + I + s
    elif member.decltype == ast_pb2.Decl.Type.CLASS:
      if member.class_.name.native == '__iter__':
        assert len(member.class_.members) == 1, (
            '__iter__ class must have only one "def", '
            f'{len(member.class_.members)} members found')
        d = member.class_.members[0]
        assert d.decltype == d.FUNC, (
            f'__iter__ class must have only func_decl members, {d.decltype} '
            'member found')
        assert d.func.name.native == '__next__', (
            '__iter__ class must have only one "def __next__", '
            f'"def {d.func.name.native}" found')
        for s in _generate_iterator(class_name, class_decl, d.func):
          yield I + I + s
      else:
        for s in generate_from(member, class_name,
                               trampoline_class_names, codegen_info):
          yield I + s

  if (not ctor_defined and class_decl.cpp_has_def_ctor and
      (not class_decl.cpp_abstract or trampoline_generated)):
    yield I + I + f'{class_name}.def(py::init<>());'

  for base in implicit_upcast_bases:
    mangled = legacy_types.Mangle(base.cpp_canonical_type)
    I2 = I + I  # pylint: disable=invalid-name
    yield I2 + f'{class_name}.def('
    yield I2 + I2 + f'"as_{mangled}",'
    yield I2 + I2 + f'[]({class_decl.name.cpp_name}* self) {{'
    yield I2 + I2 + I2 + 'return py::capsule(static_cast<void *>(self));'
    yield I2 + I2 + '}'
    yield I2 + ');'

  if not reduce_or_reduce_ex_defined:
    yield I + I + (f'{class_name}.def("__reduce_ex__",' +
                   ' ::clif_pybind11::ReduceExImpl, py::arg("protocol")=-1);')

  yield I + '}'


def _generate_iterator(
    class_name: str, class_decl: ast_pb2.ClassDecl, func_decl: ast_pb2.FuncDecl
) -> Generator[str, None, None]:
  template_param = ''
  if function_lib.has_bytes_return(func_decl):
    template_param = '<py::return_value_policy::_return_as_bytes>'
  yield (
      f'{class_name}.def("__iter__", [](const {class_decl.name.cpp_name} &s)'
      f'{{ return py::make_iterator{template_param}(s.begin(), s.end()); }}, '
      'py::keep_alive<0, 1>());')


def _generate_constructor(
    class_name: str, func_decl: ast_pb2.FuncDecl,
    class_decl: ast_pb2.ClassDecl, trampoline_generated: bool,
    codegen_info: utils.CodeGenInfo) -> Generator[str, None, None]:
  """Generates pybind11 bindings code for a constructor.

  Multiple deinitions will be generated when the constructor contains unknown
  default value arguments.

  Args:
    class_name: Name of the class that defines the contructor.
    func_decl: Constructor declaration in proto format.
    class_decl: Class declaration in proto format.
    trampoline_generated: Did we generate a trampoline for this class?
    codegen_info: The information needed to generate pybind11 code.

  Yields:
    pybind11 function bindings code.
  """
  function_lib.fix_unknown_default_value_for_unique_ptr_in_place(func_decl)
  num_unknown = function_lib.num_unknown_default_values(func_decl)
  if num_unknown:
    first_unknown_default_index = function_lib.find_first_unknown_default_index(
        func_decl)

    for unknown_default_indexes in (
        function_lib.generate_index_combination_for_unknown_default_func_decl(
            func_decl)):
      if not unknown_default_indexes:
        continue

      # Workaround: Using multiple definitions because one or more default
      # values are unknown to the code generator (due to limitations in the clif
      # matcher).
      # TODO: The workaround needs to generate 2^n function
      # overloads. Generate Python C API code instead of overloads to reduce
      # the file size when there are more than 5 params with unknown default
      # values.
      temp_func_decl = ast_pb2.FuncDecl()
      temp_func_decl.CopyFrom(func_decl)
      first_unknown_default_index = unknown_default_indexes[0]
      first_unknown_default_param = ast_pb2.ParamDecl()
      first_unknown_default_param.CopyFrom(
          temp_func_decl.params[first_unknown_default_index])
      for index in unknown_default_indexes[::-1]:
        del temp_func_decl.params[index]
      yield from _generate_constructor_overload(
          class_name, temp_func_decl, class_decl, trampoline_generated,
          codegen_info, first_unknown_default_index,
          first_unknown_default_param)
    yield from _generate_constructor_overload(
        class_name, func_decl, class_decl, trampoline_generated, codegen_info)
  else:
    yield from _generate_constructor_overload(
        class_name, func_decl, class_decl, trampoline_generated,
        codegen_info)


def _generate_constructor_overload(
    class_name: str, func_decl: ast_pb2.FuncDecl,
    class_decl: ast_pb2.ClassDecl,
    trampoline_generated: bool, codegen_info: utils.CodeGenInfo,
    first_unknown_default_index: int = -1,
    first_unknown_default_param: Optional[ast_pb2.ParamDecl] = None
) -> Generator[str, None, None]:
  """Generates pybind11 bindings code for a constructor."""
  params_list = []
  for i, param in enumerate(func_decl.params):
    params_list.append(
        function_lib.Parameter(param, f'arg{i}', codegen_info))
  params_with_types = ', '.join(
      [f'{p.cpp_type} {p.gen_name}' for p in params_list])
  params = ', '.join([p.function_argument for p in params_list])
  function_suffix = function_lib.generate_function_suffixes(
      func_decl, release_gil=False,
      first_unknown_default_index=first_unknown_default_index)
  if func_decl.name.native == '__init__' and func_decl.is_extend_method:
    yield f'{class_name}.def(py::init([]({params_with_types}) {{'
    if function_lib.unknown_default_argument_needs_non_default_value(
        params_list, first_unknown_default_index, first_unknown_default_param):
      yield I + function_lib.generate_value_error_for_unknown_default_param(
          func_decl, first_unknown_default_param)
      yield I + 'return nullptr;'
    else:
      for p in params_list:
        yield from p.preprocess()
      func_keeps_gil = function_lib.func_keeps_gil(func_decl)
      if not func_keeps_gil:
        yield I + 'py::gil_scoped_release release_gil;'
      yield I + f'return {func_decl.name.cpp_name}({params});'
    yield f'}}), {function_suffix}'

  elif func_decl.name.native == '__init__':
    cpp_name = class_decl.name.cpp_name
    if trampoline_generated:
      cpp_name = utils.trampoline_name(class_decl)
    yield f'{class_name}.def(py::init([]({params_with_types}) {{'
    if function_lib.unknown_default_argument_needs_non_default_value(
        params_list, first_unknown_default_index, first_unknown_default_param):
      yield I + function_lib.generate_value_error_for_unknown_default_param(
          func_decl, first_unknown_default_param)
      yield I + 'return nullptr;'
    else:
      for p in params_list:
        yield from p.preprocess()
      func_keeps_gil = function_lib.func_keeps_gil(func_decl)
      if not func_keeps_gil and params_with_types:
        yield I + 'py::gil_scoped_release release_gil;'
      yield I + (f'return std::make_unique<{cpp_name}>'
                 f'({params}).release();')
    yield f'}}), {function_suffix}'

  elif func_decl.constructor:
    yield (f'{class_name}.def_static("{func_decl.name.native}", '
           f'[]({params_with_types}) {{')
    if function_lib.unknown_default_argument_needs_non_default_value(
        params_list, first_unknown_default_index, first_unknown_default_param):
      yield I + function_lib.generate_value_error_for_unknown_default_param(
          func_decl, first_unknown_default_param)
      yield I + 'return nullptr;'
    else:
      for p in params_list:
        yield from p.preprocess()
      func_keeps_gil = function_lib.func_keeps_gil(func_decl)
      if not func_keeps_gil:
        yield I + 'py::gil_scoped_release release_gil;'
      yield I + (f'return std::make_unique<{class_decl.name.cpp_name}>'
                 f'({params});')
    yield f'}}, {function_suffix}'
