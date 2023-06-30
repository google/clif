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


def _generate_self_param_with_type(
    var_decl: ast_pb2.VarDecl,
    class_decl: ast_pb2.ClassDecl) -> str:
  if var_decl.is_extend_variable:
    assert var_decl.cpp_get.params
    return f'{var_decl.cpp_get.params[0].type.cpp_type} self'
  return f'{class_decl.name.cpp_name} &self'


def _generate_cpp_get(
    var_decl: ast_pb2.VarDecl,
    class_decl: ast_pb2.ClassDecl,
    generate_comma: bool = False,
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
  if _convert_ptr_to_ref(var_decl):
    ret = f'*{ret}'
    reference_internal = False
  return_value_policy = function_lib.generate_return_value_policy_for_type(
      var_decl.type, reference_internal=reference_internal
  )
  return_value_policy_pack = (
      f'py::return_value_policy_pack({return_value_policy})'
  )
  self_param_with_type = _generate_self_param_with_type(var_decl, class_decl)
  if generate_comma:
    yield I + f'py::cpp_function([]({self_param_with_type}) {{'
  else:
    yield I + f'[]({self_param_with_type}) {{'
  yield I + I + f'return {ret};'
  if generate_comma:
    yield I + f'}}, {return_value_policy_pack}),'
  else:
    yield I + f'}}, {return_value_policy_pack});'


def _generate_cpp_set(
    var_decl: ast_pb2.VarDecl,
    class_decl: ast_pb2.ClassDecl,
) -> Generator[str, None, None]:
  """Generate lambda expressions for setters."""
  yield I + (
      f'[]({class_decl.name.cpp_name}& self, {var_decl.type.cpp_type} v) {{'
  )
  value = 'v'
  if var_decl.type.cpp_type.startswith('::std::unique_ptr'):
    value = 'std::move(v)'
  yield I + I + f'self.{var_decl.name.cpp_name} = {value};'
  yield I + '});'


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
      yield from _generate_cpp_set(var_decl, class_decl)
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
  cpp_set = f'&{var_decl.cpp_set.name.cpp_name}'
  if var_decl.cpp_set.is_overloaded:
    cpp_set_cast = function_lib.generate_cpp_function_cast(
        var_decl.cpp_set, class_decl)
    cpp_set = f'{cpp_set_cast}&{var_decl.cpp_set.name.cpp_name}'
  if not var_decl.cpp_set.name.cpp_name:
    cpp_set = 'nullptr'
  if var_decl.HasField('cpp_set'):
    yield f'{class_name}.def_property("{var_decl.name.native}", '
    yield from _generate_cpp_get(var_decl, class_decl, generate_comma=True)
    yield I + f'{cpp_set});'
  else:
    yield f'{class_name}.def_property_readonly("{var_decl.name.native}", '
    yield from _generate_cpp_get(var_decl, class_decl)


def _generate_unproperty(
    class_name: str, var_decl: ast_pb2.VarDecl, class_decl: ast_pb2.ClassDecl
) -> Generator[str, None, None]:
  """Generates functions to expose attributes instead of exposing directly."""
  yield f'{class_name}.def("{var_decl.cpp_get.name.native}",'
  yield from _generate_cpp_get(var_decl, class_decl)
  if var_decl.HasField('cpp_set'):
    yield f'{class_name}.def("{var_decl.cpp_set.name.native}",'
    yield from _generate_cpp_set(var_decl, class_decl)
