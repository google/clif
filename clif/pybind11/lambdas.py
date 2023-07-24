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
"""Generates C++ lambda functions inside pybind11 bindings code."""

from typing import Generator, List, Optional

from clif.protos import ast_pb2
from clif.pybind11 import function_lib
from clif.pybind11 import operators
from clif.pybind11 import utils

I = utils.I

_NEEDS_INDEX_CHECK_METHODS = frozenset([
    '__getitem__#', '__setitem__#', '__delitem__#'
])


def generate_lambda(
    module_name: str, func_decl: ast_pb2.FuncDecl,
    codegen_info: utils.CodeGenInfo,
    class_decl: Optional[ast_pb2.ClassDecl] = None,
    first_unknown_default_index: int = -1,
    first_unknown_default_param: Optional[ast_pb2.ParamDecl] = None
) -> Generator[str, None, None]:
  """Entry point for generation of lambda functions in pybind11."""
  start_idx = 0
  if func_decl_is_extend_member_function(func_decl, class_decl):
    start_idx = 1
  params_list = []
  for i, param in enumerate(func_decl.params[start_idx:]):
    params_list.append(
        function_lib.Parameter(param, f'arg{i + 1}', codegen_info))
  if func_decl_is_extend_member_function(func_decl, class_decl):
    assert func_decl.params
    params_list = [
        function_lib.Parameter(func_decl.params[0], 'arg0', codegen_info, True)
    ] + params_list
  params_with_type = _generate_lambda_params_with_types(
      func_decl, params_list, class_decl)
  # @sequential, @context_manager
  func_name = func_decl.name.native.rstrip('#').rstrip('@')
  if class_decl is not None:
    func_name = function_lib.setstate_workaround_temp_name(func_name)
  yield (f'{module_name}.{function_lib.generate_def(func_decl)}'
         f'("{func_name}", []({params_with_type}) {{')

  # Only throw ValueError when there are parameters with unknown default value
  # and users do not provide values for it.
  if function_lib.unknown_default_argument_needs_non_default_value(
      params_list, first_unknown_default_index, first_unknown_default_param):
    yield I + function_lib.generate_value_error_for_unknown_default_param(
        func_decl, first_unknown_default_param)
  else:
    yield from generate_lambda_body(
        func_decl, params_list, codegen_info, class_decl
    )
  is_member_function = (class_decl is not None)
  function_suffix = function_lib.generate_function_suffixes(
      func_decl, release_gil=False, is_member_function=is_member_function,
      first_unknown_default_index=first_unknown_default_index)
  yield f'}}, {function_suffix}'


def generate_check_nullptr(
    func_decl: ast_pb2.FuncDecl, param_name: str) -> Generator[str, None, None]:
  yield I + f'if ({param_name} == nullptr) {{'
  yield I + I + (f'throw py::type_error("{func_decl.name.native}() '
                 f'argument {param_name} is not valid.");')
  yield I +'}'


def generate_cpp_function_return_post_process(
    func_decl: ast_pb2.FuncDecl, function_call_returns: str, self_param: str,
) -> Generator[str, None, None]:
  """Generates post process for returns values of cpp functions."""
  if func_decl.postproc == '->self':
    yield I + f'return {self_param};'
  elif func_decl.name.native == '__enter__@':
    yield I + f'return {self_param};'
  elif func_decl.name.native == '__exit__@':
    yield I + 'return py::none();'
  elif func_decl.postproc:
    assert '.' in func_decl.postproc
    module_name, method_name = func_decl.postproc.rsplit('.', maxsplit=1)
    # TODO: Port or reuse `clif::ImportFQName`.
    yield I + f'auto mod = py::module_::import("{module_name}");'
    yield I + ('py::object result_ = '
               f'mod.attr("{method_name}")({function_call_returns});')
    yield I + 'return result_;'
  elif function_call_returns:
    if len(func_decl.returns) > 1:
      yield I + f'return std::make_tuple({function_call_returns});'
    else:
      yield I + f'return {function_call_returns};'
  else:
    yield I + 'return py::none();'


def generate_lambda_body(
    func_decl: ast_pb2.FuncDecl,
    params: List[function_lib.Parameter],
    codegen_info: utils.CodeGenInfo,
    class_decl: Optional[ast_pb2.ClassDecl] = None,
) -> Generator[str, None, None]:
  """Generates body of lambda expressions."""
  function_call = generate_function_call(func_decl, class_decl)
  params_str = ', '.join([p.function_argument for p in params])
  function_call_params = generate_function_call_params(func_decl, params_str)
  cpp_void_return = func_decl.cpp_void_return or not func_decl.returns

  if (class_decl and func_decl_is_member_function(func_decl, class_decl) and
      not func_decl.is_extend_method):
    yield I + f'auto self = py::cast<{class_decl.name.cpp_name}*>(self_py);'

  # Generates void pointer check for parameters that are converted from non
  # pointers by code generator.
  for p in params:
    if p.check_nullptr:
      yield from generate_check_nullptr(func_decl, p.gen_name)
    yield from p.preprocess()

  if func_decl.name.native in _NEEDS_INDEX_CHECK_METHODS and class_decl:
    start_idx = 1 if func_decl.is_extend_method else 0
    assert len(params) >= start_idx + 1, ('sequential methods need at least '
                                          'one param')
    index = params[start_idx]
    self_param = (
        params[0].gen_name if func_decl.is_extend_method else 'self_py')
    yield I + f'py::object length_function_ = {self_param}.attr("__len__");'
    yield I + 'if (length_function_.is_none()) {'
    yield I + I + (f'throw py::attribute_error("class {class_decl.name.native} '
                   f'defined {func_decl.name.native}, but does not define '
                   '`__len__` function.");')
    yield I +'}'
    yield I + (f'Py_ssize_t {index.gen_name}_ = ::clif::item_index('
               f'{index.gen_name}, py::cast<int>(length_function_()));')
    yield I + (f'if ({index.gen_name}_ < 0) {{')
    yield I + I + 'throw py::index_error("index out of range.");'
    yield I +'}'
    yield I + f'{index.gen_name} = {index.gen_name}_;'

  if not cpp_void_return:
    ret0 = func_decl.returns[0]
    if not ret0.type.cpp_type:
      yield I + 'py::cpp_function ret0;'
    else:
      yield I + 'py::object ret0;'

  # Generates declarations of pointer return values outside of scope
  for i, r in enumerate(func_decl.returns):
    if i or cpp_void_return:
      yield I + f'{r.type.cpp_type} ret{i}{{}};'

  yield I + '{'
  func_keeps_gil = function_lib.func_keeps_gil(func_decl)
  if not func_keeps_gil:
    yield I + I + 'py::gil_scoped_release gil_release;'

  # Generates call to the wrapped function
  cpp_void_return = func_decl.cpp_void_return or not func_decl.returns
  if not cpp_void_return:
    ret0 = func_decl.returns[0]
    if not ret0.type.cpp_type:
      callback_cpp_type = function_lib.generate_callback_signature(ret0)
      callback_params_list = [
          f'py::arg("{param.name.native}")'
          for param in ret0.type.callable.params]
      callback_params_str = ', '.join(callback_params_list)
      yield I + I + (f'{callback_cpp_type} ret0_ = '
                     f'{function_call}({function_call_params});')
      yield I + I + '{'
      if not func_keeps_gil:
        yield I + I + I + 'py::gil_scoped_acquire gil_acquire;'
      if callback_params_str:
        yield I + I + I + ('ret0 = py::cpp_function(ret0_, '
                           f'{callback_params_str});')
      else:
        yield I + I + I + 'ret0 = py::cpp_function(ret0_);'
      for s in _generate_python_error_check():
        yield I + I + I + s
      yield I + I + '}'
    else:
      yield I + I + (f'{ret0.type.cpp_type} ret0_ = '
                     f'{function_call}({function_call_params});')
      ret0_with_py_cast = generate_function_call_return(
          func_decl, ret0, 'ret0_', codegen_info, class_decl)
      yield I + I + '{'
      if not func_keeps_gil:
        yield I + I + I + 'py::gil_scoped_acquire gil_acquire;'
      yield I + I + I + f'ret0 = {ret0_with_py_cast};'
      for s in _generate_python_error_check():
        yield I + I + I + s
      yield I + I + '}'
  else:
    yield I + I + f'{function_call}({function_call_params});'
    for s in _generate_python_error_check(not func_keeps_gil):
      yield I + I + s
  yield I + '}'

  function_call_returns = generate_function_call_returns(
      func_decl, codegen_info, class_decl)
  # Generates returns of the lambda expression
  self_param = 'self'
  if func_decl_is_extend_member_function(func_decl, class_decl):
    self_param = params[0].gen_name
  yield from generate_cpp_function_return_post_process(
      func_decl, function_call_returns, self_param)


def generate_function_call_params(
    func_decl: ast_pb2.FuncDecl, params_str: str) -> str:
  """Generates the parameters of function calls in lambda expressions."""
  # Ignore the return value of the function itself when generating pointer
  # parameters.
  stard_idx = 0
  if not func_decl.cpp_void_return and len(func_decl.returns):
    stard_idx = 1
  pointer_params_str = ', '.join(
      [f'&ret{i}' for i in range(stard_idx, len(func_decl.returns))])

  if params_str and pointer_params_str:
    return f'{params_str}, {pointer_params_str}'
  elif pointer_params_str:
    return pointer_params_str
  else:
    return params_str


def generate_function_call_returns(
    func_decl: ast_pb2.FuncDecl, codegen_info: utils.CodeGenInfo,
    class_decl: Optional[ast_pb2.ClassDecl] = None) -> str:
  """Generates return values of cpp function."""
  all_returns_list = []
  for i, r in enumerate(func_decl.returns):
    if i == 0 and not func_decl.cpp_void_return:
      all_returns_list.append('ret0')
    else:
      ret = generate_function_call_return(
          func_decl, r, f'ret{i}', codegen_info, class_decl)
      all_returns_list.append(ret)
  return ', '.join(all_returns_list)


def generate_function_call_return(
    func_decl: ast_pb2.FuncDecl, return_value: ast_pb2.ParamDecl,
    return_value_name: str, codegen_info: utils.CodeGenInfo,
    class_decl: Optional[ast_pb2.ClassDecl] = None) -> str:
  """Generates return values of cpp function."""
  ret = f'std::move({return_value_name})'
  return_value_policy = function_lib.generate_return_value_policy_for_type(
      return_value.type
  )
  if return_value.type.lang_type in codegen_info.capsule_types:
    ret = (f'clif::CapsuleWrapper<{return_value.type.cpp_type}>'
           f'({return_value_name})')
  elif function_lib.is_status_param(return_value, codegen_info.requires_status):
    status_type = function_lib.generate_status_type(func_decl, return_value)
    ret = f'({status_type})(std::move({return_value_name}))'
  if (func_decl.return_value_policy ==
      ast_pb2.FuncDecl.ReturnValuePolicy.REFERENCE):
    return_value_policy = 'py::return_value_policy::reference'
  return_value_policy_pack = (
      f'py::return_value_policy_pack({return_value_policy})'
  )
  if func_decl_is_extend_member_function(func_decl, class_decl):
    return f'py::cast({ret}, {return_value_policy_pack}, arg0_py)'
  elif func_decl_is_member_function(func_decl, class_decl):
    return f'py::cast({ret}, {return_value_policy_pack}, self_py)'
  else:
    return f'py::cast({ret}, {return_value_policy_pack})'


def _generate_lambda_params_with_types(
    func_decl: ast_pb2.FuncDecl,
    params: List[function_lib.Parameter],
    class_decl: Optional[ast_pb2.ClassDecl] = None) -> str:
  """Generates parameters and types in the signatures of lambda expressions."""
  params_list = [f'{p.cpp_type} {p.gen_name}' for p in params]
  if (func_decl_is_member_function(func_decl, class_decl) and
      not func_decl.is_extend_method):
    params_list = ['py::object self_py'] + params_list
  # For reflected operations, we need to generate (const Type& self, int lhs)
  # instead of (int lhs, const Type& self). So swapping the two function
  # parameters.
  if func_decl.name.native in operators.REFLECTED_OPS and len(params_list) == 2:
    params_list.reverse()
  if func_decl.name.native == '__exit__@' and class_decl:
    params_list.append('py::args')
  return ', '.join(params_list)


def func_decl_is_member_function(
    func_decl: ast_pb2.FuncDecl,
    class_decl: Optional[ast_pb2.ClassDecl] = None) -> bool:
  return (class_decl and not func_decl.classmethod and
          not func_decl.cpp_opfunction)


def func_decl_is_extend_member_function(
    func_decl: ast_pb2.FuncDecl,
    class_decl: Optional[ast_pb2.ClassDecl] = None) -> bool:
  return (func_decl_is_member_function(func_decl, class_decl) and
          func_decl.is_extend_method)


def generate_function_call(
    func_decl: ast_pb2.FuncDecl,
    class_decl: Optional[ast_pb2.ClassDecl] = None) -> str:
  """Generates the function call underneath the lambda expression."""
  if (func_decl.classmethod or not class_decl or func_decl.is_extend_method or
      func_decl.cpp_opfunction):
    return func_decl.name.cpp_name
  else:
    method_name = func_decl.name.cpp_name.split('::')[-1]
    return f'self->{method_name}'


def _generate_python_error_check(
    acquire_gil: bool = False) -> Generator[str, None, None]:
  if acquire_gil:
    yield 'py::gil_scoped_acquire gil_acquire;'
  yield '::clif::ThrowErrorAlreadySetIfPythonErrorOccurred();'
