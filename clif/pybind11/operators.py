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

from clif.protos import ast_pb2
from clif.pybind11 import utils

I = utils.I


def generate_operator(module_name: str, func_decl: ast_pb2.FuncDecl,
                      operator_index: int):
  """Generates operator overload functions.

  Args:
    module_name: String containing the outer module name.
    func_decl: AST function declaration in proto format.
    operator_index: Index of the operator in cpp_name.

  Yields:
    Pybind11 operator overload bindings code.

  """

  if operator_index >= 0:
    operator = func_decl.name.cpp_name[operator_index:]
    operator = operator.strip()

    if operator in {'~'}:
      yield from _generate_unary_operator(module_name, operator)
    elif operator in {'<<', '>>'}:
      yield from _generate_shift_operator(module_name, operator)
    elif operator in utils.default_supported_op_types:
      yield from _generate_op_cast(module_name, operator, func_decl)
    elif func_decl.postproc == '->self' and func_decl.ignore_return_value:
      yield from _generate_inplace_operator(module_name, func_decl, operator)
    elif func_decl.cpp_opfunction:
      yield from _generate_default_operator(module_name, func_decl, operator)


def _generate_unary_operator(module_name: str, operator: str):
  yield f'{module_name}.def({operator}py::self);'


def _generate_op_cast(module_name: str, operator: str,
                      func_decl: ast_pb2.FuncDecl):
  if operator in {'bool'}:
    yield f'{module_name}.def("__bool__", &{func_decl.name.cpp_name});'
  else:
    yield f'{module_name}.def({operator}_(py::self));'


def _generate_shift_operator(module_name: str, operator: str):
  # TODO: Change hardcoded 'int' to be dynamic.
  yield f'{module_name}.def(py::self {operator} int());'


def _generate_default_operator(module_name: str, func_decl: ast_pb2.FuncDecl,
                               operator: str):
  params = []
  for param in func_decl.params:
    params.append(param.cpp_exact_type)

  yield (f'{module_name}.def({utils.convert_operator_param(params[0])} '
         f'{operator} {utils.convert_operator_param(params[1])});')


def _generate_inplace_operator(module_name: str, func_decl: ast_pb2.FuncDecl,
                               operator: str):
  assert len(func_decl.params) == 1
  param = utils.convert_operator_param(func_decl.params[0].cpp_exact_type)
  yield f'{module_name}.def(py::self {operator} {param});'
