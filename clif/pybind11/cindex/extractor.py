"""Implementation of a cindex based extractor."""

from typing import Text

from clang.cindex import TranslationUnit
from clif.protos import ast_pb2


# TODO: Implement the cindex extractor to fill out information of the
# CLIF AST.
def run(ast: ast_pb2.AST, cpp_source: Text) -> ast_pb2.AST:
  unused_tu = TranslationUnit.from_source(
      'clif_referenced_headers.h', ['-x', 'c++', '-std=c++17'],
      unsaved_files=[('clif_referenced_headers.h', cpp_source)])
  return ast
