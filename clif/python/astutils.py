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


def FuncReturnType(fdecl, true_cpp_type=False):
  if not fdecl.cpp_void_return and fdecl.returns:
    # Use cpp_type if cpp_exact_type is empty (eg. for C++ builtin types).
    return true_cpp_type and fdecl.returns[0].cpp_exact_type or Type(
        fdecl.returns[0])
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
  args = (list(a.cpp_exact_type or Type(a) for a in fdecl.params) +
          list(a.cpp_exact_type or Type(a)+'*' for a in fdecl.returns
               [not fdecl.cpp_void_return:]))  # Skip returns[0] if not void.
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
  if method.docstring != '':
    yield ''
    yield method.docstring
  else:
    yield '  Calls C++ function'
    # Gen C++ signature
    cname = method.name.cpp_name or method.name.native
    yield '  ' + FuncReturnType(method) + ' ' + cname + FuncParamStr(method)
