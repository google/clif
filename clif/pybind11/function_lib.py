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

"""Common utility functions for pybind11 function code generation."""
import itertools
import re
from typing import Generator, Optional, Tuple

from clif.protos import ast_pb2
from clif.pybind11 import operators
from clif.pybind11 import utils

I = utils.I

_STATUS_PATTERNS = (r'Status', r'StatusOr<(\S)+>')


class Parameter:
  """Wraps a C++ function parameter."""
  cpp_type: str  # The actual generated cpp_type in lambda expressions
  name: str  # cpp_name of this parameter
  function_argument: str  # How to pass this parameter to functions

  def __init__(self, param: ast_pb2.ParamDecl, param_name: str,
               codegen_info: utils.CodeGenInfo):
    ptype = param.type
    ctype = ptype.cpp_type
    self.ptype = ptype
    self.cpp_type = ctype
    self.gen_name = param_name
    self.function_argument = param_name
    self.check_nullptr = False
    use_address = False

    if not ptype.cpp_type:  # std::function
      self.cpp_type = generate_callback_signature(param)
      self.function_argument = f'std::move({self.gen_name})'
    # unique_ptr<T>, shared_ptr<T>
    elif (ctype.startswith('::std::unique_ptr') or
          ctype.startswith('::std::shared_ptr')):
      self.function_argument = f'std::move({self.gen_name})'
    elif is_cpp_vector(ptype):
      self.cpp_type = 'py::iterable'
      self.function_argument = f'std::move({self.gen_name}_)'
    elif is_cpp_set(ptype):
      self.cpp_type = 'py::iterable'
      self.function_argument = f'std::move({self.gen_name}_)'
    elif not ptype.cpp_raw_pointer:
      # T, [const] T&
      if ptype.cpp_toptr_conversion:
        self.cpp_type = f'{ctype}*'
        self.function_argument = f'*{param_name}'
        self.check_nullptr = True
        use_address = True
      elif ptype.cpp_abstract:  # for AbstractType &
        self.cpp_type = f'std::unique_ptr<{ctype}>'
        self.function_argument = f'*{param_name}'
        use_address = True
      elif ptype.cpp_copyable or ptype.cpp_movable:
        self.function_argument = f'std::move({self.gen_name})'
      else:  # Convering uncopyable and unmovable types to pointers
        self.cpp_type = f'{ctype}*'
        self.function_argument = f'*{param_name}'

    if ptype.lang_type in codegen_info.capsule_types:
      self.cpp_type = f'clif::CapsuleWrapper<{self.cpp_type}>'
      if use_address:
        self.function_argument = f'*{self.gen_name}.ptr'
      else:
        self.function_argument = f'{self.gen_name}.ptr'
      self.check_nullptr = False

  def preprocess(self) -> Generator[str, None, None]:
    """Generate necessary preprocess for this parameter."""
    if is_cpp_vector(self.ptype):
      yield (I + f'{self.ptype.cpp_type} {self.gen_name}_ = py::list('
             f'{self.gen_name}).release().cast<{self.ptype.cpp_type}>();')
    elif is_cpp_set(self.ptype):
      yield (I + f'{self.ptype.cpp_type} {self.gen_name}_ = py::set('
             f'{self.gen_name}).release().cast<{self.ptype.cpp_type}>();')


def is_cpp_vector(param_type: ast_pb2.Type) -> bool:
  return (param_type.cpp_type.startswith('::std::vector') and
          param_type.lang_type.startswith('list'))


def is_cpp_set(param_type: ast_pb2.Type) -> bool:
  return ((param_type.cpp_type.startswith('::std::set') or
           param_type.cpp_type.startswith('::std::unordered_set')) and
          param_type.lang_type.startswith('set'))


def func_has_vector_param(func_decl: ast_pb2.FuncDecl) -> bool:
  for param in func_decl.params:
    if is_cpp_vector(param.type):
      return True
  return False


def func_has_set_param(func_decl: ast_pb2.FuncDecl) -> bool:
  for param in func_decl.params:
    if is_cpp_set(param.type):
      return True
  return False


def num_unknown_default_values(func_decl: ast_pb2.FuncDecl) -> int:
  num_unknown = 0
  for param in func_decl.params:
    if param.default_value == 'default':
      num_unknown += 1
  return num_unknown


def generate_index_combination_for_unknown_default_func_decl(
    func_decl: ast_pb2.FuncDecl
) -> Generator[Tuple[int, ...], None, None]:
  """Generate combination of the indexes of parameters with unknown default.

  This is used to generate function overloads to handle unknown default values.
  For example, we have the following C++ function:

  ```
  int add(int a, Arg b = "some unknown default", int c = 3, int d = 4);
  ```

  Then the function returns the following combinations:
      (1,), (1, 2), (1, 3), (1, 2, 3)

  Args:
    func_decl: Function declaration in proto format.

  Yields:
    Combination of the indexes of parameters with unknown default.
  """
  num_params = len(func_decl.params)
  unknown_default_indexes = []
  for i, param in enumerate(func_decl.params):
    # Do not consider about unique_ptr because we use nullptr as default value
    # of unique_ptr when it is unknown.
    if (param.default_value == 'default'
        and not param.type.cpp_type.startswith('::std::unique_ptr')):
      unknown_default_indexes.append(i)
  if unknown_default_indexes:
    first_unknown_default_index = unknown_default_indexes[0]
    default_value_indexes = []
    for i in range(first_unknown_default_index, num_params):
      default_value_indexes.append(i)
    for i in range(len(default_value_indexes) + 1):
      for candidate in itertools.combinations(default_value_indexes, i):
        # Only yield combinations with at least one index with unknown default
        # value.
        if set(unknown_default_indexes).intersection(set(candidate)):
          yield candidate


def generate_function_suffixes(
    func_decl: ast_pb2.FuncDecl, release_gil: bool = True,
    is_member_function: bool = True, first_unknown_default_index: int = -1
) -> str:
  """Generates py_args, docstrings and return value policys."""
  py_args = generate_py_args(
      func_decl, is_member_function, first_unknown_default_index)
  suffix = ''
  if py_args:
    suffix += f'{py_args}, '
  suffix += f'{generate_return_value_policy(func_decl)}'
  if func_decl.docstring:
    suffix += f', {generate_docstring(func_decl.docstring)}'
  if release_gil and not func_decl.py_keep_gil:
    suffix += ', py::call_guard<py::gil_scoped_release>()'
  suffix += ');'
  return suffix


def generate_param_type(param: ast_pb2.ParamDecl) -> str:
  if param.type.HasField('callable'):
    return generate_callback_signature(param)
  else:
    return param.type.cpp_type


def generate_def(func_decl: ast_pb2.FuncDecl) -> str:
  static_str = '_static' if func_decl.classmethod else ''
  return f'def{static_str}'


def generate_cpp_function_cast(
    func_decl: ast_pb2.FuncDecl,
    class_decl: Optional[ast_pb2.ClassDecl] = None) -> str:
  """Generates a method signature for each function.

  Args:
    func_decl: Function declaration in proto format.
    class_decl: Outer class declaration in proto format. None if the function is
      not a member of a class.

  Returns:
    The signature of the function.
  """

  params_list_types = []
  for param in func_decl.params:
    if param.type.HasField('callable'):
      params_list_types.append(generate_callback_signature(param))
    elif not utils.is_usable_cpp_exact_type(param.cpp_exact_type):
      params_list_types.append(param.type.cpp_type)
    else:
      params_list_types.append(param.cpp_exact_type)
  for ret in func_decl.returns[1:]:
    if not utils.is_usable_cpp_exact_type(ret.cpp_exact_type):
      params_list_types.append(ret.type.cpp_type)
    else:
      params_list_types.append(ret.cpp_exact_type)
  params_str_types = ', '.join(params_list_types)

  return_type = ''
  if func_decl.cpp_void_return:
    return_type = 'void'
  elif func_decl.returns:
    if (func_decl.returns[0].type.cpp_type.startswith('::std::shared_ptr') or
        func_decl.returns[0].type.cpp_type.startswith('::std::unique_ptr')):
      return_type = func_decl.returns[0].type.cpp_type
    else:
      return_type = func_decl.returns[0].cpp_exact_type
  elif func_decl.name.cpp_name.endswith('operator=') and class_decl:
    return_type = f'{class_decl.name.cpp_name}&'
  if not return_type:
    return_type = 'void'

  class_sig = ''
  if class_decl and not (func_decl.cpp_opfunction or
                         func_decl.is_extend_method or
                         func_decl.classmethod):
    class_sig = f'{class_decl.name.cpp_name}::'
    if func_decl.postproc == '->self' and func_decl.ignore_return_value:
      return_type = class_decl.name.cpp_name

  cpp_const = ''
  if func_decl.cpp_const_method:
    cpp_const = ' const'
  return f'({return_type} ({class_sig}*)({params_str_types}){cpp_const})'


def generate_callback_signature(param: ast_pb2.ParamDecl) -> str:
  """Generate signatures for callback functions."""
  func_decl = param.type.callable
  params_list_types = []
  for param in func_decl.params:
    params_list_types.append(param.cpp_exact_type)
  params_str_types = ', '.join(params_list_types)
  if func_decl.cpp_void_return or not func_decl.returns:
    return_type = 'void'
  else:
    if not func_decl.returns[0].cpp_exact_type:
      return_type = func_decl.returns[0].type.cpp_type
    else:
      return_type = func_decl.returns[0].cpp_exact_type
  return f'::std::function<{return_type}({params_str_types})>'


def generate_py_args(func_decl: ast_pb2.FuncDecl,
                     is_member_function: bool = True,
                     first_unknown_default_index: int = -1) -> str:
  """Generates bindings code for function parameter declarations."""
  params_list = []
  for i, param in enumerate(func_decl.params):
    if ((param.name.native == 'self' or param.name.native == 'cls') and
        is_member_function):
      continue
    if first_unknown_default_index == -1:
      if (param.default_value and param.default_value != 'default'):
        params_list.append(_generate_py_arg_with_default(param))
      else:
        params_list.append(f'py::arg("{param.name.cpp_name}")')
    elif (i < first_unknown_default_index and param.default_value and
          param.default_value != 'default'):
      params_list.append(_generate_py_arg_with_default(param))
    else:
      params_list.append(f'py::arg("{param.name.cpp_name}")')
  # Insert `py::kw_only()` at the index of the first parameter with unknown
  # default value so that pybind11 is not confused about which overload to use.
  if first_unknown_default_index != -1 and params_list:
    params_list.insert(first_unknown_default_index, 'py::kw_only()')
  operators.fix_py_args_for_unsupported_operators_in_place(
      func_decl, params_list)
  return ', '.join(params_list)


def _generate_py_arg_with_default(param: ast_pb2.ParamDecl) -> str:
  if param.default_value == 'nullptr':
    return f'py::arg("{param.name.cpp_name}") = {param.default_value}'
  else:
    return (f'py::arg("{param.name.cpp_name}") = '
            f'static_cast<{param.type.cpp_type}>({param.default_value})')


def generate_docstring(docstring: str) -> str:
  docstring = docstring.strip().replace('\n', r'\n').replace('"', r'\"')
  return f'"{docstring}"'


def is_bytes_type(pytype: ast_pb2.Type) -> bool:
  return pytype.lang_type == 'bytes' or '<bytes>' in pytype.lang_type


def has_bytes_return(func_decl: ast_pb2.FuncDecl) -> bool:
  for r in func_decl.returns:
    if is_bytes_type(r.type):
      return True
  return False


def is_status_param(param: ast_pb2.ParamDecl, requires_status: bool) -> bool:
  if not requires_status:
    return False
  for pattern in _STATUS_PATTERNS:
    if re.fullmatch(pattern, param.type.lang_type):
      return True
  return False


def is_status_callback(param: ast_pb2.ParamDecl,
                       requires_status: bool) -> bool:
  if not requires_status:
    return False
  if not param.type.cpp_type and len(param.type.callable.returns):
    callback_return = param.type.callable.returns[0]
    for pattern in _STATUS_PATTERNS:
      if re.fullmatch(pattern, callback_return.type.lang_type):
        return True
  return False


def generate_status_type(func_decl: ast_pb2.FuncDecl,
                         param: ast_pb2.ParamDecl) -> str:
  if func_decl.marked_non_raising:
    return f'pybind11::google::NoThrowStatus<{param.type.cpp_type}>'
  else:
    return param.type.cpp_type


def type_has_py_object_param(pytype: ast_pb2.Type) -> bool:
  if pytype.lang_type == 'object':
    return True
  for child_type in pytype.params:
    if type_has_py_object_param(child_type):
      return True
  return False


def func_has_py_object_params(func_decl: ast_pb2.FuncDecl) -> bool:
  for p in func_decl.params:
    if type_has_py_object_param(p.type):
      return True
  for r in func_decl.returns:
    if type_has_py_object_param(r.type):
      return True
  return False


def func_keeps_gil(func_decl: ast_pb2.FuncDecl) -> bool:
  if func_has_py_object_params(func_decl):
    return True
  if func_decl.py_keep_gil:
    return True
  return False


def generate_return_value_policy(func_decl: ast_pb2.FuncDecl) -> str:
  """Generates pybind11 return value policy based on function return type.

  Emulates the behavior of the generated Python C API code.

  Args:
    func_decl: The function declaration that needs to be processed.

  Returns:
    pybind11 return value policy based on the function return value.
  """
  prefix = 'py::return_value_policy::'
  if has_bytes_return(func_decl):
    return prefix + '_return_as_bytes'
  if func_decl.cpp_void_return or not func_decl.returns:
    return prefix + 'automatic'
  if func_decl.HasField('return_value_policy'):
    if func_decl.return_value_policy == ast_pb2.FuncDecl.AUTOMATIC_REFERENCE:
      return prefix + 'automatic_reference'
    if func_decl.return_value_policy == ast_pb2.FuncDecl.TAKE_OWNERSHIP:
      return prefix + 'take_ownership'
    if func_decl.return_value_policy == ast_pb2.FuncDecl.COPY:
      return prefix + 'copy'
    if func_decl.return_value_policy == ast_pb2.FuncDecl.MOVE:
      return prefix + 'move'
    if func_decl.return_value_policy == ast_pb2.FuncDecl.REFERENCE:
      return prefix + 'reference'
    if func_decl.return_value_policy == ast_pb2.FuncDecl.REFERENCE_INTERNAL:
      return prefix + 'reference_internal'
    if func_decl.return_value_policy == ast_pb2.FuncDecl.RETURN_AS_BYTES:
      return prefix + '_return_as_bytes'
    return prefix + 'automatic'
  return_type = func_decl.returns[0]
  # For smart pointers, it is unnecessary to specify a return value policy in
  # pybind11.
  if re.match('::std::unique_ptr<.*>', return_type.cpp_exact_type):
    return prefix + 'automatic'
  elif re.match('::std::shared_ptr<.*>', return_type.cpp_exact_type):
    return prefix + 'automatic'
  elif return_type.type.cpp_raw_pointer:
    # Const pointers to uncopyable object are not supported by PyCLIF.
    if return_type.cpp_exact_type.startswith('const '):
      return prefix + 'copy'
    else:
      return prefix + 'reference'
  elif return_type.cpp_exact_type.endswith('&'):
    if return_type.cpp_exact_type.startswith('const '):
      return prefix + 'copy'
    elif return_type.type.cpp_movable:
      return prefix + 'move'
    else:
      return prefix + 'automatic'
  else:  # Function returns objects directly.
    if return_type.type.cpp_movable:
      return prefix + 'move'
    elif return_type.type.cpp_copyable:
      return prefix + 'copy'
  return prefix + 'automatic'
