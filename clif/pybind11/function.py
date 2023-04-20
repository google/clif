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

"""Generates pybind11 bindings code for functions."""

from typing import Generator, Optional

from clif.protos import ast_pb2
from clif.pybind11 import function_lib
from clif.pybind11 import lambdas
from clif.pybind11 import unknown_default_value
from clif.pybind11 import utils


I = utils.I


def generate_from(
    module_name: str, func_decl: ast_pb2.FuncDecl,
    codegen_info: utils.CodeGenInfo,
    class_decl: Optional[ast_pb2.ClassDecl] = None,
) -> Generator[str, None, None]:
  """Generates pybind11 bindings code for functions.

  Args:
    module_name: String containing the superclass name.
    func_decl: Function declaration in proto format.
    codegen_info: The information needed to generate pybind11 code.
    class_decl: Outer class declaration in proto format. None if the function is
      not a member of a class.

  Yields:
    pybind11 function bindings code.
  """
  num_unknown = function_lib.num_unknown_default_values(func_decl)
  if num_unknown:
    first_unknown_default_index = function_lib.find_first_unknown_default_index(
        func_decl)

    # For functions with unknown default values, we need to generate 2^n
    # overloaded functions as a workaround (due to limitations in the clif
    # matcher). This might increase the size of the generated code by a lot.
    # Therefore when there are more than 5 params with unknown default values
    # (2^5=32 overloads), we decide to generate Python C API code instead of
    # overloads to reduce the file size.
    if len(func_decl.params) - first_unknown_default_index >= 5:
      yield from unknown_default_value.generate_from(
          module_name, func_decl, codegen_info, class_decl)
    else:
      function_lib.fix_unknown_default_value_for_unique_ptr_in_place(func_decl)
      yield from _generate_overload_for_unknown_default_function(
          module_name, func_decl, codegen_info, class_decl)
  else:
    yield from _generate_function(
        module_name, func_decl, codegen_info, class_decl)


def _generate_function(
    module_name: str, func_decl: ast_pb2.FuncDecl,
    codegen_info: utils.CodeGenInfo,
    class_decl: Optional[ast_pb2.ClassDecl] = None,
) -> Generator[str, None, None]:
  """Generates pybind11 bindings code for ast_pb2.FuncDecl."""
  yield from lambdas.generate_lambda(
      module_name, func_decl, codegen_info, class_decl)


def _generate_overload_for_unknown_default_function(
    module_name: str, func_decl: ast_pb2.FuncDecl,
    codegen_info: utils.CodeGenInfo,
    class_decl: Optional[ast_pb2.ClassDecl] = None,
) -> Generator[str, None, None]:
  """Generate multiple definitions for functions with unknown default values.

  For example, we have the following C++ function:
  ```
  int add(int a, Arg b = "some unknown default", int c = 3);
  ```

  Then the following overloads are generated:
  ```
    m.def("add", [](int a, Arg b, int c) {
      return add(a, b, c);
    }, py::arg("a"), py::arg("b"), py::arg("c") = 3);
    m.def("add", [](int a, int c) {  // -b
      throw py::value_error("argument b needs a non-default value");
    }, py::arg("a"), py::kw_only(), py::arg("c"));
    m.def("add", [](int a) {  // -b, -c
      return add(a);
    }, py::arg("a"));
  ```

  Args:
    func_decl: Function declaration in proto format.

  Yields:
    Combination of the indexes of parameters with unknown default.

  Args:
    module_name: String containing the superclass name.
    func_decl: Function declaration in proto format.
    codegen_info: The information needed to generate pybind11 code.
    class_decl: Outer class declaration in proto format. None if the function is
      not a member of a class.

  Yields:
    pybind11 function bindings code.
  """
  for unknown_default_indexes in (
      function_lib.generate_index_combination_for_unknown_default_func_decl(
          func_decl)):
    if not unknown_default_indexes:
      continue

    # Workaround: Using multiple definitions because one or more default values
    # are unknown to the code generator (due to limitations in the clif
    # matcher).
    temp_func_decl = ast_pb2.FuncDecl()
    temp_func_decl.CopyFrom(func_decl)
    first_unknown_default_index = unknown_default_indexes[0]
    first_unknown_default_param = ast_pb2.ParamDecl()
    first_unknown_default_param.CopyFrom(
        temp_func_decl.params[first_unknown_default_index])
    for index in unknown_default_indexes[::-1]:
      del temp_func_decl.params[index]
    yield from lambdas.generate_lambda(
        module_name, temp_func_decl, codegen_info, class_decl,
        first_unknown_default_index, first_unknown_default_param)
  yield from _generate_function(
      module_name, func_decl, codegen_info, class_decl)
