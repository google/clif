# Copyright 2017 Google Inc.
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

"""AST accessors."""

import itertools


def HaveEnum(decls):
  return (any(d.decltype == d.ENUM for d in decls) or
          any(HaveEnum(d.class_.members) for d in decls
              if d.decltype == d.CLASS))


def Type(p):
  return p.type.cpp_type


def ExactTypeOrType(p, cpp_type_suffix=''):
  # Use cpp_type if cpp_exact_type is empty (eg. for C++ builtin types).
  return p.cpp_exact_type or Type(p) + cpp_type_suffix


def TypeMaybeConst(p):
  # Crude band-aid to unblock PyCLIF-C-API / PyCLIF-pybind11 convergence.
  # Fixing this properly probably requires deeper concerted fixes in the
  # matcher and the two code generators.
  if (
      p.cpp_exact_type
      and p.cpp_exact_type.startswith('const ')
      and p.cpp_exact_type.endswith('*')
      and not p.type.cpp_type.startswith('const ')
  ):
    return 'const ' + p.type.cpp_type
  return p.type.cpp_type


def FuncReturnType(fdecl, true_cpp_type=False):
  if not fdecl.cpp_void_return and fdecl.returns:
    return (ExactTypeOrType if true_cpp_type else TypeMaybeConst)(
        fdecl.returns[0]
    )
  return 'void'


def TupleStr(alist):
  return '(%s)' % ', '.join(alist)


def FuncReturns(fdecl, true_cpp_type=False):
  return_type = FuncReturnType(fdecl, true_cpp_type)
  return (Type(a) + '*' for a in fdecl.returns[return_type != 'void':])


def StdFuncParamStr(fdecl):
  """Constructs the "(params)" string for the std::function declaration."""
  return (FuncReturnType(fdecl, true_cpp_type=True) +
          TupleStr(a.cpp_exact_type for a in fdecl.params))


def FuncParamStr(fdecl, arg_name=None, true_cpp_type=False):
  """Constructs the "(params)" string for the func declaration proto."""
  if not arg_name:
    return TupleStr(itertools.chain((Type(a) for a in fdecl.params),
                                    FuncReturns(fdecl)))
  assert true_cpp_type, 'arg_name make sense only for true_cpp_type'
  # Skip returns[0] if not void.
  returns = fdecl.returns if fdecl.cpp_void_return else fdecl.returns[1:]
  args = ([ExactTypeOrType(a) for a in fdecl.params] +
          [ExactTypeOrType(a, '*') for a in returns])
  return TupleStr('%s %s%d' % (a, arg_name, i) for i, a in enumerate(args))


def Docstring(method):
  """Generate method:FuncDecl docstring one line at a time."""
  res = [a.name.native + ':' + a.type.lang_type for a in method.returns]
  out = ''  # Default None output not printed.
  if res:
    out = TupleStr(res) if len(res) > 1 else method.returns[0].type.lang_type
    out = ' -> ' + out
  i = TupleStr(a.name.native + ':' + a.type.lang_type +
               ('=default' if a.default_value else '') for a in method.params)
  # Gen Python signature
  yield method.name.native + i + out
  # Docstring provided in the CLIF file.
  for line in method.docstring.splitlines():
    if str is bytes:  # PY2
      yield line.encode('unicode-escape')
    else:
      yield line
  yield '  Calls C++ function'
  # Gen C++ signature
  cname = method.name.cpp_name or method.name.native
  yield '  ' + FuncReturnType(method) + ' ' + cname + FuncParamStr(method)
