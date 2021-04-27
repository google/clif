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

from typing import Generator

from clif.protos import ast_pb2
from clif.pybind11 import utils

I = utils.I

UNARY_OPS = {
    '__neg__': ('operator-', '~'),
    '__pos__': ('operator+', '+'),
    '__invert__': ('operator~', '~'),
    '__bool__': ('operator bool', '!'),
    '__int__': ('operator int', 'int_'),
    '__float__': ('operator float', 'float_'),
}

BINARY_OPS = {
    '__sub__': ('operator-', '-'),
    '__add__': ('operator+', '+'),
    '__mul__': ('operator*', '*'),
    '__div__': ('operator/', '/'),
    '__truediv__': ('operator/', '/'),
    '__mod__': ('operator%', '%'),
    '__lshift__': ('operator<<', '<<'),
    '__rshift__': ('operator>>', '>>'),
    '__and__': ('operator&', '&'),
    '__xor__': ('operator^', '^'),
    '__eq__': ('operator==', '=='),
    '__ne__': ('operator!=', '!='),
    '__or__': ('operator|', '|'),
    '__gt__': ('operator>', '>'),
    '__ge__': ('operator>=', '>='),
    '__lt__': ('operator<', '<'),
    '__le__': ('operator<=', '<='),
}

INPLACE_OPS = {
    '__iadd__': ('operator+=', '+='),
    '__isub__': ('operator-=', '-='),
    '__imul__': ('operator*=', '*='),
    '__idiv__': ('operator/=', '/='),
    '__ifloordiv__': ('operator/=', '/='),
    '__itruediv__': ('operator/=', '/='),
    '__imod__': ('operator%=', '%='),
    '__ilshift__': ('operator<<=', '<<='),
    '__irshift__': ('operator>>=', '>>='),
    '__iand__': ('operator&=', '&='),
    '__ixor__': ('operator^=', '^='),
    '__ior__': ('operator|=', '|='),
}

REFLECTED_OPS = {
    '__radd__': ('operator+', '+'),
    '__rsub__': ('operator-', '-'),
    '__rmul__': ('operator*', '*'),
    '__rdiv__': ('operator/', '/'),
    '__rtruediv__': ('operator/', '/'),
    '__rfloordiv__': ('operator/', '/'),
    '__rmod__': ('operator%', '%'),
    '__rlshift__': ('operator<<', '<<'),
    '__rrshift__': ('operator>>', '>>'),
    '__rand__': ('operator&', '&'),
    '__rxor__': ('operator~', '~'),
    '__ror__': ('operator|', '|'),
}

SUPPORTED_OPS = {**UNARY_OPS, **BINARY_OPS, **INPLACE_OPS, **REFLECTED_OPS}


def needs_operator_overloading(func_decl: ast_pb2.FuncDecl) -> bool:
  """Returns whether operator overloading is needed for the function."""
  py_name = func_decl.name.native
  assert len(SUPPORTED_OPS) == sum(len(d) for d in [
      UNARY_OPS, BINARY_OPS, INPLACE_OPS, REFLECTED_OPS])
  if py_name not in SUPPORTED_OPS:
    return False
  expected_operator = SUPPORTED_OPS.get(py_name)[0]
  # If user does not use the pre-defined operator for a magic method,
  # we just fall back to normal function generation.
  operator_name = func_decl.name.cpp_name.split('::')[-1]
  return operator_name == expected_operator


def generate_operator(
    module_name: str,
    func_decl: ast_pb2.FuncDecl) -> Generator[str, None, None]:
  """Generates operator overload functions.

  Args:
    module_name: String containing the outer module name.
    func_decl: AST function declaration in proto format.

  Yields:
    Pybind11 operator overload bindings code.
  """

  py_name = func_decl.name.native
  if py_name in UNARY_OPS:
    yield _generate_unary_operator(module_name, func_decl)
  elif py_name in BINARY_OPS:
    yield _generate_binary_operator(module_name, func_decl)
  elif py_name in INPLACE_OPS:
    yield _generate_inplace_operator(module_name, func_decl)
  elif py_name in REFLECTED_OPS:
    yield _generate_reflected_operator(module_name, func_decl)
  else:
    yield ''


def _generate_unary_operator(module_name: str,
                             func_decl: ast_pb2.FuncDecl) -> str:
  py_name = func_decl.name.native
  assert py_name in UNARY_OPS, f'unsupported unary operator: {py_name}'
  operator = UNARY_OPS[func_decl.name.native][1]
  return f'{module_name}.def({operator}(py::self));'


def _generate_binary_operator(module_name: str,
                              func_decl: ast_pb2.FuncDecl) -> str:
  """Generates bindings code for binary operators."""
  py_name = func_decl.name.native
  assert py_name in BINARY_OPS, f'unsupported binary operator: {py_name}'
  assert func_decl.params, f'function {py_name} does not have any parameters'
  operator = BINARY_OPS[func_decl.name.native][1]
  if len(func_decl.params) == 1:
    param = func_decl.params[0].cpp_exact_type
  else:
    param = func_decl.params[1].cpp_exact_type
  right_operand = _convert_param_to_operand(param)
  return f'{module_name}.def(py::self {operator} {right_operand});'


def _generate_inplace_operator(module_name: str,
                               func_decl: ast_pb2.FuncDecl) -> str:
  py_name = func_decl.name.native
  assert py_name in INPLACE_OPS, f'unsupported inplace operator: {py_name}'
  assert func_decl.params, f'function {py_name} does not have any parameters'
  operator = INPLACE_OPS[func_decl.name.native][1]
  operand = _convert_param_to_operand(func_decl.params[0].cpp_exact_type)
  return f'{module_name}.def(py::self {operator} {operand});'


def _generate_reflected_operator(module_name: str,
                                 func_decl: ast_pb2.FuncDecl) -> str:
  py_name = func_decl.name.native
  assert py_name in REFLECTED_OPS, f'unsupported reflected operator: {py_name}'
  assert func_decl.params, f'function {py_name} does not have any parameters'
  operator = REFLECTED_OPS[func_decl.name.native][1]
  left_operand = _convert_param_to_operand(func_decl.params[0].cpp_exact_type)
  return f'{module_name}.def({left_operand} {operator} py::self);'


def _convert_param_to_operand(param: str) -> str:
  if '::' in param:
    return 'py::self'
  else:
    return f'{param}()'
