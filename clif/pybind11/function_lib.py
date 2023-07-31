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
from typing import Generator, List, Optional, Tuple

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
               codegen_info: utils.CodeGenInfo, is_self_param: bool = False):
    ptype = param.type
    ctype = ptype.cpp_type
    self.ptype = ptype
    self.cpp_type = ctype
    self.original_param_name = param_name
    self.gen_name = param_name
    self.function_argument = param_name
    self.check_nullptr = False
    self.is_self_param = is_self_param
    use_address = False

    is_smart_ptr = (ctype.startswith('::std::unique_ptr') or
                    ctype.startswith('::std::shared_ptr'))
    self.is_ptr = ptype.cpp_raw_pointer or is_smart_ptr
    if is_self_param:
      self.cpp_type = 'py::object'
      self.gen_name = f'{param_name}_py'
      if self.is_ptr:
        self.function_argument = param_name
      else:
        self.function_argument = f'*{param_name}'
    elif not ptype.cpp_type:  # std::function
      self.cpp_type = generate_callback_signature(param)
      self.function_argument = f'std::move({self.gen_name})'
    # unique_ptr<T>, shared_ptr<T>
    elif is_smart_ptr:
      self.function_argument = f'std::move({self.gen_name})'
    elif ptype.cpp_raw_pointer:
      if (not ptype.cpp_toptr_conversion and ctype.endswith('*')
          and ptype.cpp_has_public_dtor and not ptype.cpp_abstract
          and ptype.cpp_has_def_ctor):
        # Create a copy on stack and pass its address.
        # For compatibility with the original C API code generator.
        self.cpp_type = ctype[:-1]
        self.function_argument = f'&{param_name}'
    else:
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
    if self.is_self_param:
      cpp_type = f'{self.ptype.cpp_type}*'
      if self.is_ptr:
        cpp_type = self.ptype.cpp_type
      yield I + (f'auto {self.original_param_name} = '
                 f'{self.gen_name}.cast<{cpp_type}>();')


def num_unknown_default_values(func_decl: ast_pb2.FuncDecl) -> int:
  num_unknown = 0
  for param in func_decl.params:
    if param.default_value == 'default':
      num_unknown += 1
  return num_unknown


def fix_unknown_default_value_for_unique_ptr_in_place(
    func_decl: ast_pb2.FuncDecl) -> None:
  """Assume the default value of std::unique_ptr is nullptr."""
  for param in func_decl.params:
    if (param.type.cpp_type.startswith('::std::unique_ptr') and
        param.default_value == 'default'):
      param.default_value = 'nullptr'


def find_first_unknown_default_index(func_decl: ast_pb2.FuncDecl) -> int:
  for i, param in enumerate(func_decl.params):
    if param.default_value == 'default':
      return i
  return -1


def unknown_default_argument_needs_non_default_value(
    params_list: List[Parameter],
    first_unknown_default_index: int,
    first_unknown_default_param: ast_pb2.ParamDecl) -> bool:
  return (first_unknown_default_index != -1 and first_unknown_default_param and
          len(params_list) > first_unknown_default_index)


def generate_value_error_for_unknown_default_param(
    func_decl: ast_pb2.FuncDecl, first_unknown_default_param: ast_pb2.ParamDecl
) -> str:
  return (f'throw py::value_error("{func_decl.name.native}() argument '
          f'{first_unknown_default_param.name.native} needs a non-default '
          'value");')


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


def generate_return_value_policy_for_type(
    param_type: ast_pb2.Type,
    is_callable_arg: bool = False,
    reference_internal: bool = False,
) -> str:
  """Generate return value policy for possibly nested types."""
  if param_type.params:
    return_value_policy_list = []
    for child_param_type in param_type.params:
      return_value_policy_list.append(
          generate_return_value_policy_for_type(
              child_param_type, is_callable_arg, reference_internal
          )
      )
    return_value_policy_str = ', '.join(return_value_policy_list)
    if len(return_value_policy_list) > 1:
      return f'{{{return_value_policy_str}}}'
    else:
      return ('py::return_value_policy_pack(std::vector<'
              f'py::return_value_policy_pack>({{{return_value_policy_str}}}), '
              'py::return_value_policy::_clif_automatic)')
  else:
    if param_type.lang_type == 'bytes':
      return 'py::return_value_policy::_return_as_bytes'
    elif is_callable_arg:
      return 'py::return_value_policy::automatic_reference'
    elif reference_internal:
      return 'py::return_value_policy::reference_internal'
    else:
      return 'py::return_value_policy::_clif_automatic'


def generate_return_value_policy_for_func_decl_params(
    func_decl: ast_pb2.FuncDecl,
) -> str:
  """Generate return value policy for all parameters of a function."""
  return_value_policy_list = []
  for param in func_decl.params:
    return_value_policy = generate_return_value_policy_for_type(
        param.type, is_callable_arg=True
    )
    if len(param.type.params) > 1:
      return_value_policy_list.append(f'{{{return_value_policy}}}')
    else:
      return_value_policy_list.append(return_value_policy)
  if return_value_policy_list:
    return_value_policy_str = ', '.join(return_value_policy_list)
    if len(return_value_policy_list) > 1:
      return f'{{{return_value_policy_str}}}'
    else:
      return return_value_policy_str
  else:
    return 'py::return_value_policy::_clif_automatic'


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
  if func_decl.name.native in operators.ALL_OPS:
    suffix += 'py::is_operator(), '
  suffix += 'py::return_value_policy::_clif_automatic'
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
    return_value_policy_pack = _generate_return_value_policy_pack_for_py_arg(
        param
    )
    if first_unknown_default_index == -1:
      if (param.default_value and param.default_value != 'default'):
        params_list.append(
            _generate_py_arg_with_default(param, return_value_policy_pack)
        )
      else:
        params_list.append(
            _generate_py_arg_without_default(param, return_value_policy_pack)
        )
    elif (i < first_unknown_default_index and param.default_value and
          param.default_value != 'default'):
      params_list.append(
          _generate_py_arg_with_default(param, return_value_policy_pack)
      )
    else:
      params_list.append(
          _generate_py_arg_without_default(param, return_value_policy_pack)
      )
  # Insert `py::kw_only()` at the index of the first parameter with unknown
  # default value so that pybind11 is not confused about which overload to use.
  if first_unknown_default_index != -1 and params_list:
    params_list.insert(first_unknown_default_index, 'py::kw_only()')
  operators.fix_py_args_for_operators_in_place(
      func_decl, params_list)
  return ', '.join(params_list)


def _generate_py_arg_with_default(
    param: ast_pb2.ParamDecl, return_value_policy_pack: str
) -> str:
  """Generate `py::arg` for parameters with default value."""
  if return_value_policy_pack:
    if param.default_value == 'nullptr':
      return (
          f'py::arg("{param.name.cpp_name}")'
          f'.policies({return_value_policy_pack}) = {param.default_value}'
      )
    else:
      return (
          f'py::arg("{param.name.cpp_name}")'
          f'.policies({return_value_policy_pack}) = '
          f'static_cast<{param.type.cpp_type}>({param.default_value})'
      )
  else:
    if param.default_value == 'nullptr':
      return f'py::arg("{param.name.cpp_name}") = {param.default_value}'
    else:
      return (
          f'py::arg("{param.name.cpp_name}") = '
          f'static_cast<{param.type.cpp_type}>({param.default_value})'
      )


def _generate_py_arg_without_default(
    param: ast_pb2.ParamDecl, return_value_policy_pack: str
) -> str:
  if return_value_policy_pack:
    return (
        f'py::arg("{param.name.cpp_name}").policies({return_value_policy_pack})'
    )
  else:
    return f'py::arg("{param.name.cpp_name}")'


def _generate_return_value_policy_pack_for_py_arg(
    param: ast_pb2.ParamDecl,
) -> str:
  policy = ''
  if param.type.HasField('callable'):
    policy = generate_return_value_policy_for_func_decl_params(
        param.type.callable
    )
  if policy:
    return f'py::return_value_policy_pack({policy})'
  else:
    return ''


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


# The pair of setstate_workaround_* functions below is to sidestep this
# special-case code in pybind11:
# https://github.com/pybind/pybind11/blob/a500f439d06d220ee2c680cdd2c8828eac8e7dfc/include/pybind11/pybind11.h#L370
# For easy reference, the code there is:
#        rec->is_constructor = (std::strcmp(rec->name, "__init__") == 0)
#                              || (std::strcmp(rec->name, "__setstate__") == 0);
# In the context of PyCLIF-pybind11, __setstate__ needs to be a normal method,
# not an alternative constructor. To not have to modify the pybind11 sources,
# class_::def() is passed a temporary name. After the member function is bound
# to the temporary name as a normal function, it is reassigned to the
# __setstate__ attribute, and the temporary attribute is deleted.
def setstate_workaround_temp_name(func_name):
  if func_name != '__setstate__':
    return func_name
  return '__setstate_clif_pybind11__'


def setstate_workaround_move_attr(class_name, func_name):
  if func_name == '__setstate__':
    yield (
        f'{class_name}.attr("__setstate__")' +
        f' = {class_name}.attr("__setstate_clif_pybind11__");')
    yield f'py::delattr({class_name}, "__setstate_clif_pybind11__");'
