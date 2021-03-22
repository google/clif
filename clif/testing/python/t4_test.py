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

"""Tests for clif.testing.python.t4."""


from absl.testing import absltest
from absl.testing import parameterized

from clif.protos import ast_pb2
from clif.testing import nested_pb2

from clif.testing.python import t4
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import t4_pybind11
except ImportError:
  t4_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (t4, t4_pybind11))
    if np[1] is not None
])
class T4Test(absltest.TestCase):

  def testProtoParam(self, wrapper_lib):
    pb = ast_pb2.AST()
    self.assertEqual(wrapper_lib.Walk(pb), 0)
    self.assertEqual(wrapper_lib.Size(pb), 0)

  def testProtoNestedParam(self, wrapper_lib):
    pb = ast_pb2.Decl()
    pb.decltype = pb.FUNC
    self.assertEqual(wrapper_lib.DeclType(pb), pb.FUNC)
    self.assertEqual(wrapper_lib.DeclTypeUI(pb), pb.FUNC)
    self.assertEqual(wrapper_lib.DeclTypeUO(pb), pb.FUNC)

  def testProtoNestedMessage(self, wrapper_lib):
    pb = nested_pb2.Outer.Inner()
    pb.val = pb.B
    self.assertEqual(wrapper_lib.nested(pb), pb.B)

  def testProtoVectorRaw(self, wrapper_lib):
    pbs = wrapper_lib.all_ast_borrowed()
    self.assertLen(pbs, 3)
    for a, b in zip(pbs, '123'):
      self.assertIsInstance(a, ast_pb2.AST)
      self.assertEqual(a.source, b)

  def testProtoVectorUniq(self, wrapper_lib):
    pbs = wrapper_lib.all_ast_holds()
    self.assertLen(pbs, 3)
    for a, b in zip(pbs, '123'):
      self.assertIsInstance(a, ast_pb2.AST)
      self.assertEqual(a.source, b)

  def testAsMessage(self, wrapper_lib):
    pbs = wrapper_lib.all_ast_holds()
    self.assertLen(pbs, 3)
    ast = pbs[0]
    self.assertIsInstance(ast, ast_pb2.AST)
    self.assertEqual(ast.DESCRIPTOR.full_name, 'clif.protos.AST')
    self.assertEqual(wrapper_lib.ByteSize_R(ast), 3)
    self.assertEqual(wrapper_lib.ByteSize_P(ast), 3)

  def testWrongMessageType(self, wrapper_lib):
    with self.assertRaises(TypeError):
      wrapper_lib.Walk(ast_pb2.Decl())

  def testReturnSmartPtr(self, wrapper_lib):
    wrapper_lib.GetUniquePtr(ast_pb2.Decl())
    wrapper_lib.GetSharedPtr(ast_pb2.Decl())

  def testReturnProto(self, wrapper_lib):
    pb = nested_pb2.Outer.Inner()

    pb.repeated_bytes_val.append(b'repeated')
    pb.scalar_bytes_val = b'scalar'
    actual = wrapper_lib.ReturnProto(pb)

    self.assertEqual(actual.scalar_bytes_val, b'scalar')
    self.assertEqual(actual.repeated_bytes_val, [b'repeated'])

    # We check the types to make sure that the memoryview (py3) or
    # buffer (py2) that is passed to the protos is correctly converted
    # to bytes
    self.assertIsInstance(actual.scalar_bytes_val, bytes)
    self.assertIsInstance(actual.repeated_bytes_val[0], bytes)


if __name__ == '__main__':
  absltest.main()
