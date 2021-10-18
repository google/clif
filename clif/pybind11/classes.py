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

from typing import Generator, Set

from clif.protos import ast_pb2
from clif.pybind11 import enums
from clif.pybind11 import function
from clif.pybind11 import function_lib
from clif.pybind11 import utils
from clif.pybind11 import variables

I = utils.I


def generate_from(
    class_decl: ast_pb2.ClassDecl, superclass_name: str,
    python_override_class_name: str, capsule_types: Set[str]
) -> Generator[str, None, None]:
  """Generates a complete py::class_<>.

  Args:
    class_decl: Class declaration in proto format.
    superclass_name: String name of the superclass.
    python_override_class_name: Virtual function class name.
    capsule_types: A list of C++ types that are defined as capsules.

  Yields:
    pybind11 class bindings code.
  """
  yield I + '{'
  class_name = f'{class_decl.name.native}_class'
  definition = f'py::classh<{class_decl.name.cpp_name}'
  if not class_decl.suppress_upcasts:
    for base in class_decl.bases:
      if base.HasField('cpp_name'):
        definition += f', {base.cpp_name}'
  if python_override_class_name:
    definition += f', {python_override_class_name}'
  definition += (f'> {class_name}({superclass_name}, '
                 f'"{class_decl.name.native}"')
  if class_decl.HasField('docstring'):
    definition += f', {_as_cpp_string_literal(class_decl.docstring)}'
  if class_decl.enable_instance_dict:
    definition += ', py::dynamic_attr()'
  if class_decl.final:
    definition += ', py::is_final()'
  definition += ');'
  yield I + I + definition

  constructor_defined = False
  trampoline_generated = False
  for member in class_decl.members:
    if member.decltype == ast_pb2.Decl.Type.CONST:
      for s in _generate_const_members(class_name, member):
        yield I + I + s
    elif member.decltype == ast_pb2.Decl.Type.FUNC:
      if member.func.constructor:
        constructor_defined = True
        for s in _generate_constructor(class_name, member.func, class_decl):
          yield I + I + s
      else:
        for s in function.generate_from(
            class_name, member.func, capsule_types, class_decl):
          yield I + I + s
      if member.func.virtual:
        trampoline_generated = True
    elif member.decltype == ast_pb2.Decl.Type.VAR:
      for s in variables.generate_from(class_name, member.var, class_decl):
        yield I + I + s
    elif member.decltype == ast_pb2.Decl.Type.ENUM:
      for s in enums.generate_from(class_name, member.enum):
        yield I + I + s
    elif member.decltype == ast_pb2.Decl.Type.CLASS:
      for s in generate_from(member.class_, class_name,
                             python_override_class_name, capsule_types):
        yield I + s

  if (not constructor_defined and class_decl.cpp_has_def_ctor and
      (not class_decl.cpp_abstract or trampoline_generated)):
    yield I + I + f'{class_name}.def(py::init<>());'
  yield I + '}'


def _generate_constructor(
    class_name: str, func_decl: ast_pb2.FuncDecl,
    class_decl: ast_pb2.ClassDecl) -> Generator[str, None, None]:
  """Generates constructor methods."""
  params_with_types = ', '.join(
      [f'{p.type.cpp_type} {p.name.cpp_name}' for p in func_decl.params])
  params = ', '.join([f'{p.name.cpp_name}' for p in func_decl.params])
  cpp_types = ', '.join(
      [f'{function_lib.generate_param_type(p)}' for p in func_decl.params])
  if func_decl.name.native == '__init__' and func_decl.is_extend_method:
    yield f'{class_name}.def(py::init([]({params_with_types}) {{'
    yield I + f'return {func_decl.name.cpp_name}({params});'
    yield f'}}), {function_lib.generate_function_suffixes(func_decl)}'

  elif func_decl.name.native == '__init__':
    yield (f'{class_name}.def(py::init<{cpp_types}>(), '
           f'{function_lib.generate_function_suffixes(func_decl)}')

  elif func_decl.constructor:
    yield (f'{class_name}.def_static("{func_decl.name.native}", '
           f'[]({params_with_types}) {{')
    yield I + f'return {class_decl.name.cpp_name}({params});'
    yield f'}}, {function_lib.generate_function_suffixes(func_decl)}'


def _generate_const_members(
    class_name: str, member: ast_pb2.Decl) -> Generator[str, None, None]:
  """Generates const member functions."""
  yield (f'{class_name}.def_readonly_static("{member.const.name.native}", '
         f'&{member.const.name.cpp_name});')


def _as_cpp_string_literal(s: str) -> str:
  return f'"{repr(s)}"'
