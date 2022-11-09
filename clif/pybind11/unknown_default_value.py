# Copyright 2022 Google LLC
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

"""Generates bindings code for functions with unknown default values."""
from typing import Generator, Optional

from clif.protos import ast_pb2
from clif.pybind11 import function_lib
from clif.pybind11 import lambdas
from clif.pybind11 import utils
from clif.python import gen


I = utils.I


def generate_from(
    module_name: str, func_decl: ast_pb2.FuncDecl,
    codegen_info: utils.CodeGenInfo,
    class_decl: Optional[ast_pb2.ClassDecl] = None,
) -> Generator[str, None, None]:
  """Generates lambda to handle functions with unknown default args."""
  func_name = func_decl.name.native.rstrip('#').rstrip('@')
  params_with_type = 'py::args args, py::kwargs kw'
  if class_decl:
    params_with_type = f'{class_decl.name.cpp_name} &self, ' + params_with_type
  yield (f'{module_name}.{function_lib.generate_def(func_decl)}'
         f'("{func_name}", []({params_with_type}) {{')

  all_params = (
      func_decl.params if not (func_decl.is_extend_method and class_decl) else
      func_decl.params[1:])
  nargs = len(all_params)
  minargs = sum(1 for p in all_params if not p.default_value)
  yield I + f'PyObject* a[{nargs}]{{}};'
  yield I + 'const char* names[] = {'
  for param in all_params:
    yield I + I + f'"{param.name.native}",'
  yield I + I + 'nullptr'
  yield I + '};'
  args_signature = ('O' * nargs if minargs == nargs else
                    'O' * minargs + '|' + 'O' * (nargs - minargs))
  yield I + ('if (!PyArg_ParseTupleAndKeywords(args.ptr(), kw.ptr(), '
             f'"{args_signature}:{func_decl.name.native}",')
  args_array = ', '.join(f'&a[{i}]' for i in range(nargs))
  yield I + I + I + f'const_cast<char**>(names), {args_array})) {{'
  yield I + I + (f'throw py::value_error("{func_decl.name.native}() argument '
                 'parsing failed");')
  yield I + '}'

  if minargs < nargs:
    yield I + 'int nargs;  // Find how many args actually passed in.'
    yield I + f'for (nargs = {nargs}; nargs > {minargs}; --nargs) {{'
    yield I + I + 'if (a[nargs-1] != nullptr) break;'
    yield I + '}'

  params = []
  for i, p in enumerate(all_params):
    n = i + 1
    arg = f'arg{n}'
    check_nullptr, arg_declaration = gen.CreateInputParameter(
        func_decl.name.native, p, arg, params)
    yield I + arg_declaration
    arg_cpp_type = arg_declaration[:arg_declaration.rfind(' ')]
    if i < minargs:
      yield I + f'{arg} = py::cast<{arg_cpp_type}>(py::handle(a[{i}]));'
      if check_nullptr:
        yield from lambdas.generate_check_nullptr(func_decl, arg)
    else:
      yield I + f'if (nargs > {i}) {{'
      if p.default_value == 'default':
        if n < nargs:
          if p.type.cpp_type.startswith('::std::unique_ptr'):
            yield I + I + (f'if (!a[{i}]) {{ /* default-constructed smartptr */'
                           '}')
            yield I + I + (f'else {arg} = py::cast<{arg_cpp_type}> '
                           f'(py::handle(a[{i}]))')
          else:
            yield I + I + f'if (!a[{i}]) {{'
            yield I + I + I + (
                f'throw py::value_error("{func_decl.name.native}() argument '
                f'{p.name.native} needs a non-default value");')
            yield I + I + '}'
            yield I + I + (f'else {arg} = py::cast<{arg_cpp_type}>'
                           f'(py::handle(a[{i}]));')
        else:
          yield I + I + f'{arg} = py::cast<{arg_cpp_type}>(py::handle(a[{i}]));'
        if check_nullptr:
          for line in lambdas.generate_check_nullptr(func_decl, arg):
            yield I + line
      else:
        yield I + I + (f'if (!a[{i}]) {arg} = ({p.type.cpp_type})'
                       f'{p.default_value};')
        yield I + I + (f'else {arg} = py::cast<{arg_cpp_type}>'
                       f'(py::handle(a[{i}]));')
        if check_nullptr:
          for line in lambdas.generate_check_nullptr(func_decl, arg):
            yield I + line
      yield I + '}'

  cpp_void_return = func_decl.cpp_void_return or not func_decl.returns

  # Generates declarations of return values
  for i, r in enumerate(func_decl.returns):
    if i or cpp_void_return:
      yield I + f'{r.type.cpp_type} ret{i}{{}};'
  if not cpp_void_return:
    ret0_cpp_type = lambdas.generate_return_value_cpp_type(
        func_decl, codegen_info)
    yield I + f'{ret0_cpp_type} ret0;'

  if not function_lib.func_keeps_gil(func_decl):
    yield I + 'PyThreadState* _save;'
    yield I + 'Py_UNBLOCK_THREADS'

  # Generates call to the C++ function
  function_call = lambdas.generate_function_call(func_decl, class_decl)
  function_call_returns = lambdas.generate_function_call_returns(
      func_decl, codegen_info.capsule_types)
  yield I + 'switch (nargs) {'
  for n in range(minargs, nargs+1):
    yield I + I + f'case {n}:'
    params_str = ', '.join(params[:n])
    if func_decl.is_extend_method and class_decl:
      params_str = 'self, ' + params_str
    function_call_params = lambdas.generate_function_call_params(
        func_decl, params_str)
    cpp_function_call = f'{function_call}({function_call_params})'
    if not cpp_void_return:
      yield I + I + I + f'ret0 = {cpp_function_call};'
    else:
      yield I + I + I + f'{cpp_function_call};'
    yield I + I + I + 'break;'
  yield I + '}'
  if not function_lib.func_keeps_gil(func_decl):
    yield I + 'Py_BLOCK_THREADS'

  # Generates post process for the return values.
  yield from lambdas.generate_cpp_function_return_post_process(
      func_decl, function_call_returns, 'self')
  yield '});'
