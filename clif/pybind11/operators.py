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

from typing import Generator, List, Optional

from clif.protos import ast_pb2
from clif.pybind11 import utils

I = utils.I

UNARY_OPS = {
    '__neg__': ('operator-', '-'),
    '__pos__': ('operator+', '+'),
    '__inv__': ('operator~', '~'),
    '__invert__': ('operator~', '~'),
    '__bool__': ('operator bool', '!'),
    '__int__': ('operator int', 'int_'),
    # pybind11 requires `operator double` for `__float__`. See
    # https://third_party/pybind11/include/pybind11/operators.h;l=191;rcl=480132896
    '__float__': ('operator double', 'float_'),
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
    '__rmod__': ('operator%', '%'),
    '__rlshift__': ('operator<<', '<<'),
    '__rrshift__': ('operator>>', '>>'),
    '__rand__': ('operator&', '&'),
    '__rxor__': ('operator~', '~'),
    '__ror__': ('operator|', '|'),
}

SUPPORTED_OPS = {**UNARY_OPS, **BINARY_OPS, **INPLACE_OPS, **REFLECTED_OPS}

UNSUPPORTED_BINARY_OPS = frozenset([
    '__floordiv__',
])

UNSUPPORTED_INPLACE_OPS = frozenset([
    '__ifloordiv__',
])

UNSUPPORTED_REFLECTED_OPS = frozenset([
    '__rfloordiv__',
])


def fix_py_args_for_unsupported_operators_in_place(
    func_decl: ast_pb2.FuncDecl, py_args: List[str]) -> None:
  """Fix `py::args` declaration of the operator.

  Sometimes users might implement operators as free functions, not C++ member
  functions. In this case, PyCLIF AST will include an extra parameter for
  `self`. When generating pybind11 bindings code, we always generate
  operators as member functions, therefore we need to remove `self` from the
  parameter list.

  Args:
    func_decl: AST function declaration in proto format.
    py_args: A list of strings that are like `py::arg('a')`.
  """
  py_name = func_decl.name.native

  if len(py_args) == 2:
    if py_name in UNSUPPORTED_BINARY_OPS or py_name in UNSUPPORTED_INPLACE_OPS:
      py_args.pop(0)
    elif py_name in UNSUPPORTED_REFLECTED_OPS:
      py_args.pop()


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
    func_decl: ast_pb2.FuncDecl,
    class_decl: Optional[ast_pb2.ClassDecl] = None
) -> Generator[str, None, None]:
  """Generates operator overload functions.

  Args:
    module_name: String containing the outer module name.
    func_decl: AST function declaration in proto format.
    class_decl: Outer class declaration in proto format. None if this is not
      a member function.

  Yields:
    Pybind11 operator overload bindings code.
  """

  py_name = func_decl.name.native
  class_py_name = _get_class_py_name(func_decl, class_decl)
  assert class_py_name, f'Invalid operator declaration: {func_decl}'
  if py_name in UNARY_OPS:
    yield _generate_unary_operator(module_name, func_decl)
  elif py_name in BINARY_OPS:
    yield _generate_binary_operator(module_name, func_decl, class_py_name)
  elif py_name in INPLACE_OPS:
    yield _generate_inplace_operator(module_name, func_decl, class_py_name)
  elif py_name in REFLECTED_OPS:
    yield _generate_reflected_operator(module_name, func_decl, class_py_name)
  else:
    yield ''


def _get_class_py_name(func_decl: ast_pb2.FuncDecl,
                       class_decl: Optional[ast_pb2.ClassDecl] = None) -> str:
  """Finds the Python name of the class that defines the operator function."""
  if class_decl:
    return class_decl.name.native

  if (func_decl.name.native in UNARY_OPS or
      func_decl.name.native in BINARY_OPS or
      func_decl.name.native in INPLACE_OPS):
    return func_decl.params[0].name.native
  elif func_decl.name.native in REFLECTED_OPS:
    return func_decl.params[-1].name.native
  return ''


def _generate_unary_operator(module_name: str,
                             func_decl: ast_pb2.FuncDecl) -> str:
  py_name = func_decl.name.native
  assert py_name in UNARY_OPS, f'unsupported unary operator: {py_name}'
  operator = UNARY_OPS[func_decl.name.native][1]
  return f'{module_name}.def({operator}(py::self));'


def _generate_binary_operator(module_name: str,
                              func_decl: ast_pb2.FuncDecl,
                              class_py_name: str) -> str:
  """Generates bindings code for binary operators."""
  py_name = func_decl.name.native
  assert py_name in BINARY_OPS, f'unsupported binary operator: {py_name}'
  assert func_decl.params, f'function {py_name} does not have any parameters'
  operator = BINARY_OPS[func_decl.name.native][1]
  if len(func_decl.params) == 1:
    param = func_decl.params[0]
  else:
    param = func_decl.params[1]
  right_operand = _convert_param_to_operand(param, class_py_name)
  return f'{module_name}.def(py::self {operator} {right_operand});'


def _generate_inplace_operator(module_name: str,
                               func_decl: ast_pb2.FuncDecl,
                               class_py_name: str) -> str:
  py_name = func_decl.name.native
  assert py_name in INPLACE_OPS, f'unsupported inplace operator: {py_name}'
  assert func_decl.params, f'function {py_name} does not have any parameters'
  operator = INPLACE_OPS[func_decl.name.native][1]
  operand = _convert_param_to_operand(func_decl.params[0], class_py_name)
  return f'{module_name}.def(py::self {operator} {operand});'


def _generate_reflected_operator(module_name: str,
                                 func_decl: ast_pb2.FuncDecl,
                                 class_py_name: str) -> str:
  py_name = func_decl.name.native
  assert py_name in REFLECTED_OPS, f'unsupported reflected operator: {py_name}'
  assert func_decl.params, f'function {py_name} does not have any parameters'
  operator = REFLECTED_OPS[func_decl.name.native][1]
  left_operand = _convert_param_to_operand(func_decl.params[0], class_py_name)
  return f'{module_name}.def({left_operand} {operator} py::self);'


def _convert_param_to_operand(param: ast_pb2.ParamDecl,
                              class_py_name: str) -> str:
  if param.type.lang_type == class_py_name:
    return 'py::self'
  else:
    return f'({param.type.cpp_type}){{}}'
