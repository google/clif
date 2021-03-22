# Copyright 2020 Google LLC
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


from absl.testing import absltest
from absl.testing import parameterized

from clif.protos import ast_pb2

from clif.testing.python import shared_ptr_proto_member
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import shared_ptr_proto_member_pybind11
except ImportError:
  shared_ptr_proto_member_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (shared_ptr_proto_member,
                                             shared_ptr_proto_member_pybind11))
    if np[1] is not None
])
class SharedPtrProtoMemberTest(absltest.TestCase):

  def testProtoHolderByValue(self, wrapper_lib):
    ast = ast_pb2.AST()
    ast.source = 'depot'
    ph = wrapper_lib.ProtoHolderByValue(ast)
    self.assertEqual(ph.GetByValue().source, 'depot')
    self.assertEqual(ph.GetConstRef().source, 'depot')
    self.assertIsNone(ph.ResetSource('pool'))
    self.assertEqual(ph.GetConstRef().source, 'pool')
    self.assertEqual(ast.source, 'depot')

  def testProtoHolderUniquePtr(self, wrapper_lib):
    ast = ast_pb2.AST()
    ast.source = 'depot'
    ph = wrapper_lib.ProtoHolderUniquePtr(ast)
    self.assertEqual(ph.GetUniquePtr().source, 'depot')
    # HAVE actual unique_ptr semantics returning unique_ptr from C++ to Python:
    self.assertIsNone(ph.GetUniquePtr())
    ph = wrapper_lib.ProtoHolderUniquePtr(ast)
    self.assertIsNone(ph.ResetSource('pool'))
    self.assertEqual(ph.GetUniquePtr().source, 'pool')
    # NO actual unique_ptr semantics in __init__ (passing from Python to C++):
    self.assertEqual(ast.source, 'depot')

  def testProtoHolderSharedPtr(self, wrapper_lib):
    ast = ast_pb2.AST()
    ast.source = 'depot'
    ph = wrapper_lib.ProtoHolderSharedPtr(ast)
    self.assertEqual(ph.GetSharedPtrUseCount(), 1)
    sp1 = ph.GetSharedPtr()
    # NO actual shared_ptr semantics returning shared_ptr from C++ to Python:
    self.assertEqual(ph.GetSharedPtrUseCount(), 1)
    self.assertEqual(sp1.source, 'depot')
    self.assertIsNone(ph.ResetSource('pool'))
    sp2 = ph.GetSharedPtr()
    self.assertEqual(sp2.source, 'pool')
    # NO actual shared_ptr semantics in __init__ (passing from Python to C++):
    self.assertEqual(ast.source, 'depot')
    # Each shared_ptr return actually makes a new copy of the proto:
    self.assertEqual(sp1.source, 'depot')


if __name__ == '__main__':
  absltest.main()
