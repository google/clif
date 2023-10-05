# Copyright 2021 Google LLC
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
"""Generates pybind11 bindings code for variables."""

from typing import Generator

from clif.protos import ast_pb2
from clif.pybind11 import function_lib
from clif.pybind11 import utils

I = utils.I


def _convert_ptr_to_ref(var_decl: ast_pb2.VarDecl) -> bool:
  return (
      not var_decl.type.cpp_abstract
      and not var_decl.type.cpp_type.startswith('::std::shared_ptr')
      and (
          var_decl.type.cpp_raw_pointer
          or var_decl.type.cpp_type.startswith('::std::unique_ptr')
      )
  )


def _generate_self_param_type_for_cpp_get(
    var_decl: ast_pb2.VarDecl,
    class_decl: ast_pb2.ClassDecl) -> str:
  if var_decl.is_extend_variable:
    assert var_decl.cpp_get.params
    return var_decl.cpp_get.params[0].cpp_exact_type
  return f'{class_decl.name.cpp_name}&'


def _generate_self_param_type_for_cpp_set(
    var_decl: ast_pb2.VarDecl,
    class_decl: ast_pb2.ClassDecl) -> str:
  if var_decl.is_extend_variable:
    assert var_decl.cpp_set.params
    return var_decl.cpp_set.params[0].cpp_exact_type
  return f'{class_decl.name.cpp_name}&'


def _is_var_decl_type_cpp_copyable(var_decl: ast_pb2.VarDecl) -> bool:
  if not var_decl.cpp_get.returns:
    return var_decl.type.cpp_copyable
  else:
    return var_decl.cpp_get.returns[0].type.cpp_copyable


def _generate_cpp_get(
    var_decl: ast_pb2.VarDecl,
    class_decl: ast_pb2.ClassDecl,
    generate_comma: bool = False,
    is_unproperty: bool = False,
) -> Generator[str, None, None]:
  """Generate lambda expressions for getters."""
  reference_internal = True
  if var_decl.is_extend_variable:
    ret = f'{var_decl.cpp_get.name.cpp_name}(self)'
  elif var_decl.cpp_get.name.cpp_name:
    function_name = var_decl.cpp_get.name.cpp_name.split('::')[-1]
    ret = f'self.{function_name}()'
  else:
    ret = f'self.{var_decl.name.cpp_name}'
  if not is_unproperty and _convert_ptr_to_ref(var_decl):
    ret = f'*{ret}'
    reference_internal = False
  return_value_policy = function_lib.generate_return_value_policy_for_type(
      var_decl.type, reference_internal=reference_internal
  )
  return_value_policy_pack = (
      f'py::return_value_policy_pack({return_value_policy})'
  )

  if not _is_var_decl_type_cpp_copyable(var_decl):
    yield from _generate_cpp_get_for_uncopyable_type(
        var_decl, class_decl, return_value_policy_pack, ret,
        generate_comma=generate_comma)
  else:
    yield from _generate_cpp_get_for_copyable_type(
        var_decl, class_decl, return_value_policy_pack, ret,
        generate_comma=generate_comma)


def _generate_cpp_get_for_copyable_type(
    var_decl: ast_pb2.VarDecl,
    class_decl: ast_pb2.ClassDecl,
    return_value_policy_pack: str,
    ret: str,
    generate_comma: bool = False,
) -> Generator[str, None, None]:
  """Generate lambda expressions for getters when the type is copyable."""
  self_param_type = _generate_self_param_type_for_cpp_get(var_decl, class_decl)
  if generate_comma:
    yield I + f'py::cpp_function([]({self_param_type} self) {{'
  else:
    yield I + f'[]({self_param_type} self) {{'
  yield I + I + f'return {ret};'
  if generate_comma:
    yield I + f'}}, {return_value_policy_pack}),'
  else:
    yield I + f'}}, {return_value_policy_pack});'


def _generate_cpp_get_for_uncopyable_type(
    var_decl: ast_pb2.VarDecl,
    class_decl: ast_pb2.ClassDecl,
    return_value_policy_pack: str,
    ret: str,
    generate_comma: bool = False,
) -> Generator[str, None, None]:
  """Generate lambda expressions for getters when the type is uncopyable."""
  if generate_comma:
    yield I + 'py::cpp_function([](py::object self_py) -> py::object {'
  else:
    yield I + '[](py::object self_py) -> py::object {'
  self_param_type = _generate_self_param_type_for_cpp_get(var_decl, class_decl)
  yield I + I + f'{self_param_type} self = self_py.cast<{self_param_type}>();'
  yield I + I + (f'return py::cast({ret}, {return_value_policy_pack}, '
                 'self_py);')
  if generate_comma:
    yield I + '}),'
  else:
    yield I + '});'


def _generate_cpp_set_without_setter(
    var_decl: ast_pb2.VarDecl,
    class_decl: ast_pb2.ClassDecl,
    generate_comma: bool = False,
) -> Generator[str, None, None]:
  """Generate lambda expressions for setters when setters are undefined."""
  if generate_comma:
    yield I + (f'py::cpp_function([]({class_decl.name.cpp_name}& self, '
               f'{var_decl.type.cpp_type} v) {{')
  else:
    yield I + (
        f'[]({class_decl.name.cpp_name}& self, {var_decl.type.cpp_type} v) {{'
    )
  value = 'v'
  if var_decl.type.cpp_type.startswith('::std::unique_ptr'):
    value = 'std::move(v)'
  yield I + I + f'self.{var_decl.name.cpp_name} = {value};'
  if generate_comma:
    yield I + '}));'
  else:
    yield I + '});'


def _generate_cpp_set_with_setter(
    var_decl: ast_pb2.VarDecl,
    class_decl: ast_pb2.ClassDecl,
) -> Generator[str, None, None]:
  """Generate lambda expressions for setters when setters are defined."""
  assert var_decl.cpp_set.params, (f'var_decl {var_decl.name.native} does not'
                                   'have any params.')
  self_param_type = _generate_self_param_type_for_cpp_set(var_decl, class_decl)
  yield I + (f'py::cpp_function([]({self_param_type} self, '
             f'{var_decl.cpp_set.params[-1].type.cpp_type} v) {{')
  if var_decl.is_extend_variable:
    function_call = f'{var_decl.cpp_set.name.cpp_name}(self, std::move(v))'
  else:
    method_name = var_decl.cpp_set.name.cpp_name.split('::')[-1]
    function_call = f'self.{method_name}(std::move(v))'
  yield I + I + f'{function_call};'
  yield I + '}));'


def generate_from(
    class_name: str,
    var_decl: ast_pb2.VarDecl,
    class_decl: ast_pb2.ClassDecl,
) -> Generator[str, None, None]:
  """Generates pybind11 bindings code for class attributes."""
  if var_decl.HasField('cpp_get'):
    if var_decl.cpp_get.name.native:
      yield from _generate_unproperty(class_name, var_decl, class_decl)
    else:
      yield from _generate_property(class_name, var_decl, class_decl)
  else:
    if _convert_ptr_to_ref(var_decl):
      yield f'{class_name}.def_property("{var_decl.name.native}", '
      yield from _generate_cpp_get(var_decl, class_decl, generate_comma=True)
      yield from _generate_cpp_set_without_setter(
          var_decl, class_decl, generate_comma=True)
    else:
      return_value_policy = function_lib.generate_return_value_policy_for_type(
          var_decl.type
      )
      return_value_policy_pack = (
          f'py::return_value_policy_pack({return_value_policy})'
      )
      yield (
          f'{class_name}.def_readwrite("{var_decl.name.native}", '
          f'&{class_decl.name.cpp_name}::{var_decl.name.cpp_name}, '
          f'{return_value_policy_pack});'
      )


def _generate_property(
    class_name: str, var_decl: ast_pb2.VarDecl, class_decl: ast_pb2.ClassDecl
) -> Generator[str, None, None]:
  """Generates property for simple attributes."""
  if var_decl.HasField('cpp_set'):
    yield f'{class_name}.def_property("{var_decl.name.native}", '
    yield from _generate_cpp_get(var_decl, class_decl, generate_comma=True)
    if not var_decl.cpp_set.name.cpp_name:
      yield I + 'nullptr);'
    else:
      yield from _generate_cpp_set_with_setter(var_decl, class_decl)
  else:
    yield f'{class_name}.def_property_readonly("{var_decl.name.native}", '
    yield from _generate_cpp_get(var_decl, class_decl)


def _generate_unproperty(
    class_name: str, var_decl: ast_pb2.VarDecl, class_decl: ast_pb2.ClassDecl
) -> Generator[str, None, None]:
  """Generates functions to expose attributes instead of exposing directly."""
  yield f'{class_name}.def("{var_decl.cpp_get.name.native}",'
  yield from _generate_cpp_get(var_decl, class_decl, is_unproperty=True)
  if var_decl.HasField('cpp_set'):
    yield f'{class_name}.def("{var_decl.cpp_set.name.native}",'
    yield from _generate_cpp_set_without_setter(var_decl, class_decl)
