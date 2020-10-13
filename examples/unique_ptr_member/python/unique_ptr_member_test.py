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

import unittest

from unique_ptr_member.python import unique_ptr_member


class UniquePtrMemberTest(unittest.TestCase):

  def testPointeeAndPtrOwner(self):
    obj = unique_ptr_member.pointee()
    self.assertEqual(obj.get_int(), 213)
    unique_ptr_member.ptr_owner(obj)
    with self.assertRaises(ValueError) as ctx:
      obj.get_int()
    self.assertTrue(
        str(ctx.exception).startswith('Missing value for wrapped C++ type '))

  def testCppPattern(self):
    res = unique_ptr_member.cpp_pattern()
    self.assertEqual(res, 10)


if __name__ == '__main__':
  unittest.main()
