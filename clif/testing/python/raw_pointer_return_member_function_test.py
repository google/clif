# Copyright 2023 Google LLC
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

from clif.testing.python import raw_pointer_return_member_function as tst


class RawPointerReturnMemberFunctionTest(absltest.TestCase):

  def testPersistentHolder(self):
    h = tst.DataFieldsHolder(2)
    self.assertEqual(h.vec_at(0).int_value, 13)
    self.assertEqual(h.vec_at(1).int_value, 24)

  def testTemporaryHolder(self):
    if tst.__pyclif_codegen_mode__ == 'c_api':
      self.skipTest(
          'Only PyCLIF-pybind11 handles this correctly'
          ' (avoids creating a dangling pointer).'
      )
    d = tst.DataFieldsHolder(2).vec_at(1)
    self.assertEqual(d.int_value, 24)


if __name__ == '__main__':
  absltest.main()
