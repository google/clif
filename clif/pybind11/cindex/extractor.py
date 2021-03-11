"""Implementation of a cindex based extractor.

The cindex based extractor contains very low-level manipulations of
C++ type names (stripping spaces, stars, ampersands) that are
difficult to generalize and maintain. We are exploring alternative
approaches that may allow us to avoid such manipulations.
"""

from typing import List, Optional, Text

from clang.cindex import Cursor
from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
from clang.cindex import TypeKind
from clif.protos import ast_pb2


def _get_pointee_name(type_name: Text) -> Text:
  """Remove the trailing ampersands and stars in type names."""
  type_name = type_name.strip()
  if type_name.endswith('*'):
    type_name = type_name.split('*')[0].strip()
  if type_name.endswith('&'):
    type_name = type_name.split('&')[0].strip()
  const_identifier = 'const '
  if type_name.startswith(const_identifier):
    type_name = const_identifier + type_name[len(const_identifier):].strip()
  return type_name


class Type(object):
  """Wraps a clang or a CLIF type."""

  def __init__(self, name: Text, is_pointer: bool, is_reference: bool,
               is_const: bool, pointee):
    self._name = name
    self._is_pointer = is_pointer
    self._is_reference = is_reference
    self._is_const = is_const
    self._pointee = pointee

  @classmethod
  def from_clif(cls, param_decl: ast_pb2.ParamDecl):
    """Creates a type object from CLIF ast."""
    name = param_decl.cpp_exact_type
    pointee_name = _get_pointee_name(name)
    # TODO: Make this handle reference to pointers,
    # rvalue references, pointer to pointers, pointer to constants.
    is_pointer = param_decl.cpp_exact_type.strip().endswith('*')
    is_reference = param_decl.cpp_exact_type.strip().endswith('&')
    is_const = param_decl.cpp_exact_type.strip().startswith('const ')
    if is_pointer or is_reference:
      pointee = Type(pointee_name, False, False, is_const, None)
    else:
      pointee = None
    return cls(name, is_pointer, is_reference, is_const, pointee)

  @classmethod
  def from_cindex(cls, cindex_type):
    """Creates a type object from Clang."""
    kind = cindex_type.kind

    is_pointer = kind == TypeKind.POINTER
    is_reference = kind == TypeKind.LVALUEREFERENCE
    if is_pointer or is_reference:
      pointee = Type.from_cindex(cindex_type.get_pointee())
      is_const = cindex_type.get_pointee().is_const_qualified()
    else:
      pointee = None
      is_const = cindex_type.is_const_qualified()
    name = cindex_type.spelling
    # This aims to make the object names consistent with CLIF. CLIF always add
    # global namespace prefix to objects. For example, using '::A' for object
    # 'A'. We also want to make the Type object created from cindex follow the
    # same rule.
    if kind == TypeKind.ELABORATED or kind == TypeKind.RECORD:
      if is_const:
        name = 'const ::' + name.split(' ')[-1]
      else:
        name = '::' + name
    return cls(name, is_pointer, is_reference, is_const, pointee)

  @classmethod
  def void(cls):
    return cls('void', False, False, False, None)

  def __eq__(self, other) -> bool:
    if self._is_pointer != other._is_pointer:
      return False
    if self._is_reference != other._is_reference:
      return False
    if self._is_const != other._is_const:
      return False
    if self._is_pointer or self._is_reference:
      return self._pointee == other._pointee
    else:
      return self._name == other._name

  def __repr__(self):
    pointee_name = self._pointee.name if self._pointee else 'None'
    return (
        f'Type name={self._name}, is_pointer={self._is_pointer}, '
        f'is_reference={self._is_reference}, is_const={self._is_const}, '
        f'pointee={pointee_name}')

  @property
  def name(self):
    return self._name

  @property
  def pointee_name(self):
    if self._pointee:
      return self._pointee.name
    else:
      return ''


class Function(object):
  """Wraps a clang or a CLIF Function."""

  def __init__(self, fq_name: Text, is_pure_virtual: bool,
               arguments: List[Type], return_type: List[Type]):
    self._fq_name = fq_name
    self._is_pure_virtual = is_pure_virtual
    self._arguments = arguments
    self._return_type = return_type
    self._is_overloaded = False

  @classmethod
  def from_clif(cls, func_decl: ast_pb2.Decl):
    """Create a Function object from CLIF func_decl proto."""
    fq_name = func_decl.func.name.cpp_name
    is_pure_virtual = func_decl.func.is_pure_virtual
    arguments = [Type.from_clif(x) for x in func_decl.func.params]
    if not func_decl.func.returns:
      return_type = [Type.void()]
    else:
      return_type = [Type.from_clif(x) for x in func_decl.func.returns]
    return cls(fq_name, is_pure_virtual, arguments, return_type)

  @classmethod
  def from_cindex(cls, cursor: Cursor, namespace: Text):
    """Create a Type object from cindex cursor."""
    fq_name = '::'.join([namespace, cursor.spelling])
    is_pure_virtual = cursor.is_pure_virtual_method()
    arguments = [
        Type.from_cindex(x) for x in cursor.type.argument_types()
    ]
    if cursor.type == TypeKind.VOID:
      return_type = [Type.void()]
    else:
      return_type = [
          Type.from_cindex(cursor.type.get_result())
      ]
    return cls(fq_name, is_pure_virtual, arguments, return_type)

  def __eq__(self, other) -> bool:
    if self._fq_name != other._fq_name:
      return False
    if len(self._arguments) != len(other._arguments):
      return False
    for x, fx in zip(self._arguments, other._arguments):
      if x != fx:
        return False
    return True

  def __repr__(self):
    args = ', '.join([f'{a.name}{{{a.pointee_name}}}' for a in self._arguments])
    returns = ', '.join(
        [f'{r.name}{{{r.pointee_name}}}' for r in self._return_type])
    return (
        f'Function fq_name={self._fq_name}, '
        f'is_pure_virtual={self._is_pure_virtual}, '
        f'is_overloaded={self._is_overloaded}, '
        f'arguments={args}, return_type={returns}')

  @property
  def fq_name(self):
    return self._fq_name

  @property
  def is_pure_virtual(self):
    return self._is_pure_virtual

  @property
  def is_overloaded(self):
    return self._is_overloaded

  @is_overloaded.setter
  def is_overloaded(self, is_overloaded: bool) -> None:
    self._is_overloaded = is_overloaded


class Module(object):
  """Wraps a clang AST."""

  def __init__(self, tu: TranslationUnit):
    self._func_decls_map = {}
    self._class_decl_map = {}

    self._traverse_namespace(tu.cursor, [])

  @classmethod
  def from_source(cls, source: Text, extra_flags: Optional[List[Text]] = None):
    """Create a Module object from C++ source file."""
    flags = ['-x', 'c++', '-std=c++17', '-I.']
    if extra_flags:
      flags += extra_flags
    tu = TranslationUnit.from_source(
        'clif_referenced_headers.h', flags,
        unsaved_files=[('clif_referenced_headers.h', source)])
    if tu.diagnostics:
      err_msg = '\n'.join(str(e) for e in tu.diagnostics)
      raise ValueError(f'Errors in source file: {err_msg}')
    return cls(tu)

  def query_func(self, fully_qualified_name: Text) -> List[Function]:
    return self._func_decls_map.get(fully_qualified_name, [])

  def query_class(self, fully_qualified_name: Text) -> Optional[ast_pb2.Decl]:
    return self._class_decl_map.get(fully_qualified_name)

  def _traverse_namespace(self, cursor: Cursor, namespaces: List[Text]) -> None:
    """Traverses a namespace in clang AST.

    Args:
      cursor: The cursor which is pointing to the head of the namespace.
      namespaces: The parent namespace in which the current namespace is in.
    """
    # TODO: Make this handle function or class templates.
    for c in cursor.get_children():
      if c.kind in (CursorKind.CLASS_DECL, CursorKind.STRUCT_DECL):
        self._traverse_class(c, namespaces)
      elif (c.kind == CursorKind.FUNCTION_DECL and
            c.type.kind == TypeKind.FUNCTIONPROTO):
        self._traverse_function(c, namespaces)
      elif c.kind == CursorKind.NAMESPACE:
        child_namespaces = list(namespaces)
        child_namespaces.append(c.spelling)
        self._traverse_namespace(c, child_namespaces)

  def _traverse_function(self, cursor: Cursor,
                         namespaces: List[Text]) -> None:
    """Traverses a function in clang AST and registers its declaration.

    This method modifies self._func_decl_map.

    Args:
      cursor: The cursor which is pointing to the head of a function in clang
        AST.
      namespaces: The namespace in which the function is in.
    """
    namespace = self._gen_namespace_str(namespaces)
    func_obj = Function.from_cindex(cursor, namespace)
    if func_obj.fq_name in self._func_decls_map:
      func_obj.is_overloaded = True
      if len(self._func_decls_map[func_obj.fq_name]) == 1:
        self._func_decls_map[func_obj.fq_name][0].is_overloaded = True
    else:
      self._func_decls_map[func_obj.fq_name] = []
    self._func_decls_map[func_obj.fq_name].append(func_obj)

  def _traverse_class(self, cursor: Cursor, namespaces: List[Text]) -> None:
    """Traverses a class in clang AST and registers its declaration.

    This method modifies self._class_decl_map.

    Args:
      cursor: The cursor which is pointing to the head of a class in clang AST.
      namespaces: The namespace in which the class is in.
    """
    class_decl = ast_pb2.Decl()
    class_decl.decltype = ast_pb2.Decl.Type.CLASS
    namespace = self._gen_namespace_str(namespaces)
    fully_qualified_name = '::'.join([namespace, cursor.spelling])
    for c in cursor.get_children():
      if (c.kind == CursorKind.CXX_METHOD or c.kind == CursorKind.CONSTRUCTOR
          and c.type.kind == TypeKind.FUNCTIONPROTO):
        child_namespaces = list(namespaces)
        child_namespaces.append(cursor.spelling)
        self._traverse_function(c, child_namespaces)
    self._class_decl_map[fully_qualified_name] = class_decl

  def _gen_namespace_str(self, namespaces: List[Text]) -> Text:
    if namespaces:
      return '::' + '::'.join(namespaces)
    else:
      return ''


def _fix_decl(decl: ast_pb2.Decl, module: Module) -> None:
  candidates = module.query_func(decl.func.name.cpp_name)
  function_obj = Function.from_clif(decl)
  for candidate in candidates:
    if function_obj == candidate:
      decl.func.is_pure_virtual = candidate.is_pure_virtual
      decl.func.is_overloaded = candidate.is_overloaded
      return


def _complement_matcher_ast(ast: ast_pb2.AST, module: Module) -> None:
  """Add the extra bits of information to an existing AST."""
  for decl in ast.decls:
    if decl.decltype == ast_pb2.Decl.Type.CLASS:
      for member_decl in decl.class_.members:
        if member_decl.decltype == ast_pb2.Decl.Type.FUNC:
          _fix_decl(member_decl, module)
    elif decl.decltype == ast_pb2.Decl.Type.FUNC:
      _fix_decl(decl, module)


def run(matcher_ast: ast_pb2.AST, cpp_source: Text,
        extra_flags: Optional[List[Text]] = None) -> ast_pb2.AST:
  module = Module.from_source(cpp_source, extra_flags)
  _complement_matcher_ast(matcher_ast, module)
  return matcher_ast
