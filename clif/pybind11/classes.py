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
from clif.pybind11 import consts
from clif.pybind11 import enums
from clif.pybind11 import function
from clif.pybind11 import function_lib
from clif.pybind11 import utils
from clif.pybind11 import variables

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
  if not class_decl.suppress_upcasts:
    inheritance_generated = False
    py_base = ''
    for base in class_decl.bases:
      if (base.HasField('cpp_name') and
          base.cpp_name in codegen_info.registered_types):
        definition += f', {base.cpp_name}'
        inheritance_generated = True
      elif base.native:
        py_base = base.native
    # Workaround for https://b.corp.google.com/issues/225961086#comment137
    if py_base and not inheritance_generated:
      assert py_base in codegen_info.typemap
      definition += f', {codegen_info.typemap[py_base]}'
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

  default_constructor_defined = False
  trampoline_generated = (
      utils.trampoline_name(class_decl) in trampoline_class_names)
  for member in class_decl.members:
    if member.decltype == ast_pb2.Decl.Type.CONST:
      for s in consts.generate_from(class_name, member.const):
        yield I + I + s
    elif member.decltype == ast_pb2.Decl.Type.FUNC:
      if member.func.constructor:
        # Legacy CLIF ignores __init__ for abstract classes.
        # Potential future cleanup project: generate a user-friendly error
        # instead.
        if (not class_decl.cpp_abstract or trampoline_generated) and (
            class_decl.cpp_has_def_ctor or member.func.params):
          if not member.func.params:
            default_constructor_defined = True
          for s in _generate_constructor(class_name, member.func, class_decl,
                                         trampoline_generated, codegen_info):
            yield I + I + s
      else:
        # This function will be overriden in Python. Do not call it from the
        # abstract base class.
        if class_decl.cpp_abstract and member.func.virtual:
          continue
        else:
          for s in function.generate_from(
              class_name, member.func, codegen_info, class_decl):
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

  if (not default_constructor_defined and class_decl.cpp_has_def_ctor and
      (not class_decl.cpp_abstract or trampoline_generated)):
    yield I + I + f'{class_name}.def(py::init<>());'
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
  num_unknown = function_lib.num_unknown_default_values(func_decl)
  temp_func_decl = ast_pb2.FuncDecl()
  temp_func_decl.CopyFrom(func_decl)
  if num_unknown:
    for _ in range(num_unknown):
      yield from _generate_constructor_overload(
          class_name, temp_func_decl, class_decl, trampoline_generated,
          codegen_info)
      del temp_func_decl.params[-1]
  yield from _generate_constructor_overload(
      class_name, temp_func_decl, class_decl, trampoline_generated,
      codegen_info)


def _generate_constructor_overload(
    class_name: str, func_decl: ast_pb2.FuncDecl,
    class_decl: ast_pb2.ClassDecl,
    trampoline_generated: bool, codegen_info: utils.CodeGenInfo
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
      func_decl, release_gil=False)
  if func_decl.name.native == '__init__' and func_decl.is_extend_method:
    yield f'{class_name}.def(py::init([]({params_with_types}) {{'
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
    for p in params_list:
      yield from p.preprocess()
    func_keeps_gil = function_lib.func_keeps_gil(func_decl)
    if not func_keeps_gil:
      yield I + 'py::gil_scoped_release release_gil;'
    yield I + (f'return std::make_unique<{class_decl.name.cpp_name}>'
               f'({params}).release();')
    yield f'}}, {function_suffix}'
