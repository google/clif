"""Pair of functions rewriting the ast before and after running the matcher.

Currently the matcher does not support the new @extend feature for class
methods or properties, e.g.

  class UserType:
    # Adding Python pickle support to a C++ type.
    @extend
    def __reduce_ex__(self, protocol: int) -> object

    @extend
    foo: int = property(`get_foo`, `set_foo`)

As a workaround, MoveExtendMethodsToFunctionsInPlace moves class member
func decls with is_extend_method == True out of the class context to free
functions, with self: UserType inserted as the first argument.
MoveExtendPropertiesInPlace moves property decls with
is_extend_variable == True out of the class context.

Then the matcher runs.

MoveExtendFunctionsBackIntoClassesInPlace moves the modified (by the matcher)
free function decls back into the class context. MoveExtendPropertiesInPlace
moves the modified property decls back.

IMPORTANT CAVEAT: Currently these manipulation do not support nested
classes. Using @extend for nested classes will result in a build failure
(error message from the matcher).

Implementing these two functions was the most economical and agile way to prove
that the new @extend feature is feasible. Changing matcher.cc is much more
involved in comparison, and requires 2+ weeks of waiting for a new LLVM release
that includes the changes.

Now, with the certainty that the @extend feature is feasible, and backed by
comprehensive unit tests (clif/testing/python/extend_from_clif_aux.clif),
investing effort into changing matcher.cc is probably the best path to also
cover nested classes.

The functions in this file are fully exercised indirectly by
extend_from_clif_aux_test.py. There are no direct tests, because such tests
will become obsolete when the matcher is updated, and they do not add much
value for code that is not to expected to be developed further.
"""

from clif.protos import ast_pb2

EXTEND_INFIX = '__extend__'
# Allow user to define `Class__extend__init__` instead of
# `Class__extend____init__` for extended constructors.
EXTEND_INFIX_CONSTRUCTOR = '__extend'


def MoveExtendsOutOfClassesInPlace(ast):
  MoveExtendMethodsToFunctionsInPlace(ast)
  MoveExtendPropertiesInPlace(ast)


def MoveExtendsBackIntoClassesInPlace(ast, omit_self=False):
  class_decls_by_fq_native = {}
  _BuildClassDeclsByFqNative(class_decls_by_fq_native, [], ast.decls)
  MoveExtendFunctionsBackIntoClassesInPlace(
      ast, class_decls_by_fq_native, omit_self)
  MoveExtendPropertiesBackIntoClassesInPlace(
      ast, class_decls_by_fq_native)
  FixCppHasDefaultCtor(ast)


def _BuildClassDeclsByFqNative(
    class_decls_by_fq_native, outer_class_names, members):
  """Collects fully-qualified native names (for handling nested classes)."""
  for decl in members:
    if decl.decltype == ast_pb2.Decl.Type.CLASS:
      nested_class_names = outer_class_names + [decl.class_.name]
      fq_native = '_'.join([n.native for n in nested_class_names])
      assert fq_native not in class_decls_by_fq_native
      class_decls_by_fq_native[fq_native] = decl.class_
      _BuildClassDeclsByFqNative(
          class_decls_by_fq_native, nested_class_names, decl.class_.members)


def FixCppHasDefaultCtor(ast):
  """Set cpp_has_def_ctor to True if a class has extended default ctor."""
  for decl in ast.decls:
    if decl.decltype != ast_pb2.Decl.Type.CLASS:
      continue
    if decl.class_.cpp_has_def_ctor:
      continue
    for member in decl.class_.members:
      if member.decltype != ast_pb2.Decl.Type.FUNC:
        continue
      if (member.func.is_extend_method and
          member.func.constructor and
          member.func.name.native == '__init__' and
          not member.func.params):
        decl.class_.cpp_has_def_ctor = True
        break


def _GenerateParameterSelf(class_decl, outer_class_names):
  p = ast_pb2.ParamDecl()
  p.name.native = 'self'
  p.name.cpp_name = 'self'
  nested_class_names = outer_class_names + [class_decl.name]
  p.type.lang_type = '.'.join([n.native for n in nested_class_names])
  p.type.cpp_type = '::'.join([n.cpp_name for n in nested_class_names])
  return p


def MoveExtendPropertiesInPlace(ast):
  """See module docstring."""
  extend_property_decls = []
  extend_getter_decls = []
  for decl in ast.decls:
    if decl.decltype == ast_pb2.Decl.Type.CLASS:
      _MoveExtendPropertiesInPlaceOneClass(
          extend_property_decls, extend_getter_decls, [], decl.class_)
  ast.decls.extend(extend_property_decls)
  ast.decls.extend(extend_getter_decls)


def _MoveExtendPropertiesInPlaceOneClass(
    extend_property_decls, extend_getter_decls, outer_class_names, class_decl):
  """Helper for MoveExtendPropertiesInPlace."""
  member_delete_indices = []
  for member_index, member in enumerate(class_decl.members):
    if member.decltype == ast_pb2.Decl.Type.CLASS:
      _MoveExtendPropertiesInPlaceOneClass(
          extend_property_decls, extend_getter_decls,
          outer_class_names+[class_decl.name], member.class_)
    if member.decltype != ast_pb2.Decl.Type.VAR:
      continue
    if not member.var.is_extend_variable:
      continue

    fq_native = '_'.join(
        [n.native for n in outer_class_names + [class_decl.name]])

    property_decl = ast_pb2.Decl()
    property_decl.CopyFrom(member)
    property_decl.var.name.native = (
        fq_native + EXTEND_INFIX + member.var.name.native)
    if member.var.name.cpp_name == member.var.name.native:
      property_decl.var.name.cpp_name = (
          fq_native + EXTEND_INFIX + member.var.name.cpp_name)

    p = _GenerateParameterSelf(class_decl, outer_class_names)
    property_decl.var.cpp_get.params.insert(0, p)
    property_decl.var.cpp_get.name.cpp_name = (
        fq_native + EXTEND_INFIX + member.var.cpp_get.name.cpp_name)
    if member.var.HasField('cpp_set'):
      property_decl.var.cpp_set.name.cpp_name = (
          fq_native + EXTEND_INFIX + member.var.cpp_set.name.cpp_name)
      p = _GenerateParameterSelf(class_decl, outer_class_names)
      property_decl.var.cpp_set.params.insert(0, p)
    extend_property_decls.append(property_decl)
    member_delete_indices.append(member_index)

    # generate property getters
    # (setters do not need this kind of functionality)
    getter_decl = ast_pb2.FuncDecl()
    getter_decl.CopyFrom(member.var.cpp_get)
    getter_decl.name.native = getter_decl.name.cpp_name = (
        fq_native + EXTEND_INFIX + member.var.cpp_get.name.cpp_name)
    p = _GenerateParameterSelf(class_decl, outer_class_names)
    getter_decl.params.insert(0, p)
    getter_decl.is_extend_method = True
    func_decl = ast_pb2.Decl()
    func_decl.func.CopyFrom(getter_decl)
    func_decl.decltype = ast_pb2.Decl.Type.FUNC
    extend_getter_decls.append(func_decl)

  for member_index in reversed(member_delete_indices):
    del class_decl.members[member_index]


def MoveExtendPropertiesBackIntoClassesInPlace(ast, class_decls_by_fq_native):
  """See module docstring."""
  extend_properties_orig_decl_indices = []
  for orig_decl_index, decl in enumerate(ast.decls):
    if decl.decltype != ast_pb2.Decl.Type.VAR:
      continue
    if not decl.var.is_extend_variable:
      continue
    fq_native_from_var, property_name_from_var = decl.var.name.native.split(
        EXTEND_INFIX, 1)
    target_class_decl = class_decls_by_fq_native[fq_native_from_var]
    property_decl = ast_pb2.Decl()
    property_decl.CopyFrom(decl)
    property_decl.var.name.native = property_name_from_var
    target_class_decl.members.append(property_decl)
    extend_properties_orig_decl_indices.append(orig_decl_index)
  for orig_decl_index in reversed(extend_properties_orig_decl_indices):
    del ast.decls[orig_decl_index]


def MoveExtendMethodsToFunctionsInPlace(ast):
  """See module docstring."""
  extend_methods_func_decls = []
  for decl in ast.decls:
    if decl.decltype == ast_pb2.Decl.Type.CLASS:
      _MoveExtendMethodsToFunctionsOneClass(
          extend_methods_func_decls, decl.class_, outer_class_names=[])
  ast.decls.extend(extend_methods_func_decls)


def _MoveExtendMethodsToFunctionsOneClass(
    extend_methods_func_decls, class_decl, outer_class_names):
  """Helper for MoveExtendMethodsToFunctionsInPlace."""
  member_delete_indices = []
  for member_index, member in enumerate(class_decl.members):
    if member.decltype == ast_pb2.Decl.Type.CLASS:
      _MoveExtendMethodsToFunctionsOneClass(
          extend_methods_func_decls,
          member.class_,
          outer_class_names=outer_class_names+[class_decl.name])
      continue
    if member.decltype != ast_pb2.Decl.Type.FUNC:
      continue
    if not member.func.is_extend_method:
      continue

    if member.func.classmethod:
      param0_name_native = 'cls'
    else:
      param0_name_native = 'self'
    func_decl = _MoveOutOfClassScope(
        param0_name_native, class_decl, member, outer_class_names)
    if not (member.func.classmethod or member.func.constructor):
      p = _GenerateParameterSelf(class_decl, outer_class_names)
      func_decl.func.params.insert(0, p)

    extend_methods_func_decls.append(func_decl)
    member_delete_indices.append(member_index)
  for member_index in reversed(member_delete_indices):
    del class_decl.members[member_index]


def _MoveOutOfClassScope(
    param0_name_native, class_decl, orig_func_decl, outer_class_names):
  """Helper for _MoveExtendMethodsToFunctionsOneClass."""
  func_decl = ast_pb2.Decl()
  func_decl.CopyFrom(orig_func_decl)

  fq_native = '_'.join(
      [n.native for n in outer_class_names + [class_decl.name]])
  if orig_func_decl.func.constructor:
    extend_infix = EXTEND_INFIX_CONSTRUCTOR
  else:
    extend_infix = EXTEND_INFIX
  name_native = fq_native + extend_infix + orig_func_decl.func.name.native
  name_cpp_name = fq_native + extend_infix + orig_func_decl.func.name.cpp_name

  func_decl.func.name.native = name_native
  if orig_func_decl.func.name.cpp_name == orig_func_decl.func.name.native:
    func_decl.func.name.cpp_name = name_cpp_name
  elif orig_func_decl.func.constructor:
    # cpp_name of constructors is equal to the class name. We need to change it
    # to be the extended function name.
    func_decl.func.name.cpp_name = func_decl.func.name.native

  if (func_decl.func.params and
      func_decl.func.params[0].name.native == param0_name_native):
    # A fully-qualified cpp_name was specified.
    del func_decl.func.params[0]
  return func_decl


def MoveExtendFunctionsBackIntoClassesInPlace(
    ast, class_decls_by_fq_native, omit_self):
  """See module docstring."""
  extend_methods_orig_decl_indices = []
  for orig_decl_index, decl in enumerate(ast.decls):
    if decl.decltype != ast_pb2.Decl.Type.FUNC:
      continue
    if not decl.func.is_extend_method:
      continue
    if not decl.func.classmethod and not decl.func.constructor:
      assert decl.func.params, 'extended method does not have any parameters'
      assert decl.func.params[0].name.native == 'self', (
          'the first parameter of extended method `%s` is not `self`' %
          decl.func.name.native)
    if decl.func.constructor:
      extend_infix = EXTEND_INFIX_CONSTRUCTOR
    else:
      extend_infix = EXTEND_INFIX
    fq_native_from_func, method_name_from_func = decl.func.name.native.split(
        extend_infix, 1)
    target_class_decl = class_decls_by_fq_native[fq_native_from_func]
    method_decl = ast_pb2.Decl()
    method_decl.CopyFrom(decl)
    method_decl.func.name.native = method_name_from_func
    if omit_self and not decl.func.classmethod and not decl.func.constructor:
      # Explicit self is needed for the PyCLIF code generator,
      # but confuses pytype.
      del method_decl.func.params[0]
    target_class_decl.members.append(method_decl)
    extend_methods_orig_decl_indices.append(orig_decl_index)
  for orig_decl_index in reversed(extend_methods_orig_decl_indices):
    del ast.decls[orig_decl_index]
