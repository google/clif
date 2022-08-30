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


def generate_from(
    class_name: str, var_decl: ast_pb2.VarDecl, class_decl: ast_pb2.ClassDecl
) -> Generator[str, None, None]:
  """Generates pybind11 bindings code for class attributes."""
  if var_decl.HasField('cpp_get'):
    if var_decl.cpp_get.name.native:
      yield from _generate_unproperty(class_name, var_decl, class_decl)
    else:
      yield from _generate_property(class_name, var_decl, class_decl)
  else:
    cpp_type = var_decl.type.cpp_type
    # If the wrapped attribute is raw pointer or unique_ptr, we need to do
    # special processing for it. For shared_ptr, this is unnecessary.
    if not cpp_type.startswith('::std::shared_ptr') and (
        var_decl.type.cpp_raw_pointer or
        cpp_type.startswith('::std::unique_ptr')):
      yield from _generate_pointer_attr_property(class_name, var_decl,
                                                 class_decl)
    else:
      if function_lib.is_bytes_type(var_decl.type):
        cpp_get = (f'py::cpp_function([]({class_decl.name.cpp_name} &self) '
                   f'{{ return self.{var_decl.name.cpp_name}; }}, '
                   'py::return_value_policy::_return_as_bytes)')
        cpp_set = (f'py::cpp_function([]({class_decl.name.cpp_name} &self, '
                   f'const {var_decl.type.cpp_type}& v) {{'
                   f'self.{var_decl.name.cpp_name} = v; }})')
        yield f'{class_name}.def_property("{var_decl.name.native}", '
        yield I + f'{cpp_get},'
        yield I + f'{cpp_set});'
      else:
        yield (f'{class_name}.def_readwrite("{var_decl.name.native}", '
               f'&{class_decl.name.cpp_name}::{var_decl.name.cpp_name});')


def _generate_pointer_attr_property(
    class_name: str, var_decl: ast_pb2.VarDecl, class_decl: ast_pb2.ClassDecl
) -> Generator[str, None, None]:
  """Generates property with customized getter and setter to handle pointers."""
  if not var_decl.type.cpp_copyable and not var_decl.type.cpp_movable:
    fget_body = (f'return pybind11::cast(self.{var_decl.name.cpp_name})'
                 '.release();')
  else:
    fget_body = f'return *self.{var_decl.name.cpp_name};'
  fget = (f'[]({class_decl.name.cpp_name} &self){{ '
          f'{fget_body} }}')
  value = 'v'
  # Takes ownership if the cpp attribute is unique_ptr.
  if var_decl.type.cpp_type.startswith('::std::unique_ptr'):
    value = 'std::move(v)'
  fset = (f'[]({class_decl.name.cpp_name} &self, {var_decl.type.cpp_type} v){{ '
          f'self.{var_decl.name.cpp_name} = {value}; }}')
  yield f'{class_name}.def_property("{var_decl.name.native}",'
  yield f'{fget},'
  yield f'{fset}, py::return_value_policy::reference_internal);'


def _generate_property(
    class_name: str, var_decl: ast_pb2.VarDecl, class_decl: ast_pb2.ClassDecl
) -> Generator[str, None, None]:
  """Generates property for simple attributes."""
  cpp_get = f'&{var_decl.cpp_get.name.cpp_name}'
  cpp_set = f'&{var_decl.cpp_set.name.cpp_name}'
  if function_lib.is_bytes_type(var_decl.type):
    if var_decl.is_extend_variable:
      function_call = f'{var_decl.cpp_get.name.cpp_name}(self)'
    else:
      function_name = var_decl.cpp_get.name.cpp_name.split('::')[-1]
      function_call = f'self.{function_name}()'
    cpp_get = (f'py::cpp_function([]({class_decl.name.cpp_name} &self) '
               f'{{ return {function_call}; }}, '
               'py::return_value_policy::_return_as_bytes)')
  elif var_decl.cpp_get.is_overloaded:
    cpp_get_cast = function_lib.generate_cpp_function_cast(
        var_decl.cpp_get, class_decl)
    cpp_get = f'{cpp_get_cast}&{var_decl.cpp_get.name.cpp_name}'
  if var_decl.cpp_set.is_overloaded:
    cpp_set_cast = function_lib.generate_cpp_function_cast(
        var_decl.cpp_set, class_decl)
    cpp_set = f'{cpp_set_cast}&{var_decl.cpp_set.name.cpp_name}'
  if not var_decl.cpp_get.name.cpp_name:
    cpp_get = 'nullptr'
  if not var_decl.cpp_set.name.cpp_name:
    cpp_set = 'nullptr'
  if var_decl.HasField('cpp_set'):
    yield f'{class_name}.def_property("{var_decl.name.native}", '
    yield I + f'{cpp_get},'
    yield I + f'{cpp_set});'
  else:
    yield (f'{class_name}.def_property_readonly("{var_decl.name.native}", '
           f'{cpp_get});')


def _generate_unproperty(
    class_name: str, var_decl: ast_pb2.VarDecl, class_decl: ast_pb2.ClassDecl
) -> Generator[str, None, None]:
  """Generates functions to expose attributes instead of exposing directly."""
  yield (f'{class_name}.def("{var_decl.cpp_get.name.native}", []'
         f'({class_decl.name.cpp_name} &self) {{')
  yield I + f'return self.{var_decl.name.cpp_name};'
  yield '});'
  if var_decl.HasField('cpp_set'):
    params_with_types = (
        f'{class_decl.name.cpp_name} &self, {var_decl.type.cpp_type} v')
    yield (f'{class_name}.def("{var_decl.cpp_set.name.native}", []'
           f'({params_with_types}) {{')
    yield I + f'self.{var_decl.name.cpp_name} = v;'
    yield '});'
