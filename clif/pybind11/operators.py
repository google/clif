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

from typing import List

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

ALL_OPS = frozenset(SUPPORTED_OPS.keys()).union(UNSUPPORTED_BINARY_OPS).union(
    UNSUPPORTED_INPLACE_OPS).union(UNSUPPORTED_REFLECTED_OPS)


def fix_py_args_for_operators_in_place(
    func_decl: ast_pb2.FuncDecl, py_args: List[str]) -> None:
  """Fix `pybind11::args` declaration of the operator.

  Sometimes users might implement operators as free functions, not C++ member
  functions. In this case, PyCLIF AST will include an extra parameter for
  `self`. When generating pybind11 bindings code, we always generate
  operators as member functions, therefore we need to remove `self` from the
  parameter list.

  Args:
    func_decl: AST function declaration in proto format.
    py_args: A list of strings that are like `pybind11::arg('a')`.

  Raises:
    RuntimeError: If the operator overloading has unexpected number of function
      parameters.
  """
  py_name = func_decl.name.native

  if py_name in ALL_OPS:
    if len(py_args) == 1:
      if py_name in UNARY_OPS:
        py_args.pop()
    elif len(py_args) == 2:
      if (py_name in UNSUPPORTED_BINARY_OPS or
          py_name in UNSUPPORTED_INPLACE_OPS):
        py_args.pop(0)
      elif py_name in UNSUPPORTED_REFLECTED_OPS:
        py_args.pop()
      elif py_name in BINARY_OPS or py_name in INPLACE_OPS:
        py_args.pop(0)
    elif not py_args:
      return
    else:
      raise RuntimeError(
          f'Unexpected number of function parameters: {len(py_args)=}')
