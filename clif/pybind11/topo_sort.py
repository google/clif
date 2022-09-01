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
"""Topological sort the CLIF AST."""

import collections

from clif.protos import ast_pb2


class Node:
  """Helper class for topological sort that wraps ast_pb2.ClassDecl."""

  def __init__(self, decl: ast_pb2.Decl, is_nested: bool):
    self._decl = decl
    self._requires = set()
    self._required_by = set()
    self._is_nested = is_nested

  @property
  def decl(self) -> ast_pb2.Decl:
    return self._decl

  @property
  def class_decl(self) -> ast_pb2.ClassDecl:
    return self._decl.class_

  @property
  def requires(self) -> set[str]:
    return self._requires

  @property
  def required_by(self) -> set[str]:
    return self._required_by

  @property
  def is_nested(self) -> bool:
    return self._is_nested

  def __repr__(self):
    requires = ', '.join(self._requires)
    required_by = ', '.join(self._required_by)
    return f'requires: {requires}, required_by: {required_by}'


def topo_sort_ast_in_place(ast: ast_pb2.AST) -> None:
  _topo_sort_decls_in_place(ast.decls)


def _topo_sort_decls_in_place(decls) -> None:
  """Topological sort all class decls in the same scope."""
  graph = {}

  # We split the graph construction into two functions because when initializing
  # the graph, we might not have seen all class definitions, therefore the
  # dependency information is incomplete.
  _initialize_graph(graph, decls)
  _build_graph(graph, decls)

  # Topological sort all class decls in this scope, but do not reorder nested
  # classes.
  dfs = collections.deque()
  for cpp_name, node in graph.items():
    if not node.requires:
      dfs.append(cpp_name)
  resolve_order = []
  while dfs:
    current = dfs.pop()
    if not graph[current].is_nested:
      resolve_order.append(current)
    for class_requires_current in graph[current].required_by:
      graph[class_requires_current].requires.remove(current)
      if not graph[class_requires_current].requires:
        dfs.append(class_requires_current)

  # Topological sort and reorder nested classes if exist
  for class_name in resolve_order:
    _topo_sort_decls_in_place(graph[class_name].class_decl.members)

  # Reorder the class decls in current scope
  class_decl_delete_indices = []
  for decl_index, decl in enumerate(decls):
    if decl.decltype == ast_pb2.Decl.Type.CLASS:
      class_decl_delete_indices.append(decl_index)
  for class_decl_delete_index in reversed(class_decl_delete_indices):
    del decls[class_decl_delete_index]
  for class_name in reversed(resolve_order):
    decls.insert(0, graph[class_name].decl)


def _initialize_graph(graph: dict[str, Node], members,
                      parent_class_name: str = '',
                      is_nested: bool = False) -> None:
  """Initialize the graph with class nesting information."""
  for decl in members:
    if decl.decltype == ast_pb2.Decl.Type.CLASS:
      if decl.class_.name.cpp_name not in graph:
        graph[decl.class_.name.cpp_name] = Node(decl, is_nested=is_nested)
        if parent_class_name:
          graph[decl.class_.name.cpp_name].requires.add(parent_class_name)
          graph[parent_class_name].required_by.add(decl.class_.name.cpp_name)
      _initialize_graph(graph, decl.class_.members,
                        parent_class_name=decl.class_.name.cpp_name,
                        is_nested=True)


def _build_graph(graph: dict[str, Node], members) -> None:
  """Construct the graph with class inheritance information."""
  for decl in members:
    if decl.decltype == ast_pb2.Decl.Type.CLASS:
      for base in decl.class_.bases:
        if base.cpp_name and base.cpp_name in graph:
          graph[decl.class_.name.cpp_name].requires.add(base.cpp_name)
          graph[base.cpp_name].required_by.add(decl.class_.name.cpp_name)
      _build_graph(graph, decl.class_.members)
