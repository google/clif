"""Implementation of a cindex based extractor."""

from typing import List, Optional, Text

from clang.cindex import Cursor
from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
from clang.cindex import TypeKind
from clif.protos import ast_pb2


class Module(object):
  """Wraps a clang AST."""

  def __init__(self, tu: TranslationUnit):
    self._func_decl_map = {}
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

  def query_func(self, fully_qualified_name: Text) -> Optional[ast_pb2.Decl]:
    return self._func_decl_map.get(fully_qualified_name)

  def query_class(self, fully_qualified_name: Text) -> Optional[ast_pb2.Decl]:
    return self._class_decl_map.get(fully_qualified_name)

  def _traverse_namespace(self, cursor: Cursor, namespaces: List[Text]) -> None:
    """Traverses a namespace in clang AST.

    Args:
      cursor: The cursor which is pointing to the head of the namespace.
      namespaces: The parent namespace in which the current namespace is in.
    """
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
                         namespaces: List[Text]) -> ast_pb2.Decl:
    """Traverses a function in clang AST and registers its declaration.

    This method modifies self._func_decl_map.

    Args:
      cursor: The cursor which is pointing to the head of a function in clang
        AST.
      namespaces: The namespace in which the function is in.

    Returns:
      The function declaration. This is needed so that the class decl which
        defines this function can add it as a member.
    """
    func_decl = ast_pb2.Decl()
    func_decl.decltype = ast_pb2.Decl.Type.FUNC
    func_decl.func.is_pure_virtual = cursor.is_pure_virtual_method()
    namespace = self._gen_namespace_str(namespaces)
    fully_qualified_name = '::'.join([namespace, cursor.spelling])

    self._func_decl_map[fully_qualified_name] = func_decl
    return func_decl

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
        func_decl = self._traverse_function(c, child_namespaces)
        class_decl.class_.members.append(func_decl)
    self._class_decl_map[fully_qualified_name] = class_decl

  def _gen_namespace_str(self, namespaces: List[Text]) -> Text:
    if namespaces:
      return '::' + '::'.join(namespaces)
    else:
      return ''


def _complement_matcher_ast(ast: ast_pb2.AST, module: Module) -> ast_pb2.AST:
  """Add the extra bits of information to an existing AST."""
  for decl in ast.decls:
    if decl.decltype == ast_pb2.Decl.Type.CLASS:
      for member_decl in decl.class_.members:
        if member_decl.decltype == ast_pb2.Decl.Type.FUNC:
          func_decl = module.query_func(member_decl.func.name.cpp_name)
          if func_decl:
            member_decl.func.is_pure_virtual = func_decl.func.is_pure_virtual
  return ast


def run(matcher_ast: ast_pb2.AST, cpp_source: Text,
        extra_flags: Optional[List[Text]] = None) -> ast_pb2.AST:
  module = Module.from_source(cpp_source, extra_flags)
  matcher_ast = _complement_matcher_ast(matcher_ast, module)
  return matcher_ast
