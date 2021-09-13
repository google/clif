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

"""Tests for clif.testing.python.const_pointer_return."""

from absl.testing import absltest

from clif.testing.python import const_pointer_return


class ConstPointerReturnTest(absltest.TestCase):

  def testConstPointerReturn(self):
    myclass = const_pointer_return.MyClass(100, 1000)
    # Test "const T *" as a return type, where T is a copyable class.
    self.assertEqual(const_pointer_return.Pod, type(myclass.get_pod_ptr()))
    self.assertEqual(myclass.get_pod_ptr().get_x(), 100)
    # Test "const T *" as a return type, where T is a built-in type.
    self.assertEqual(int, type(myclass.get_int_ptr()))
    self.assertEqual(myclass.get_int_ptr(), 1000)
    myclass.get_pod_ptr().set_x(10000)
    # Modification to the return value, whose C++ types is "const Pod *",
    # is not reflected at C++ side because Clif makes a copy of the return value
    # and have Python own the copy.
    self.assertEqual(myclass.get_pod_ptr().get_x(), 100)

  def testNonConstPointerCopyableReturn(self):
    myclass = const_pointer_return.MyClass2(100)
    # Test "T *" as a return type, where T is a copyable class.
    self.assertEqual(const_pointer_return.Pod, type(myclass.get_pod_ptr()))
    self.assertEqual(myclass.get_pod_ptr().get_x(), 200)
    myclass.get_pod_ptr().set_x(10000)
    # Modification to the return value, whose C++ types is "Pod *",
    # is reflected at C++ side because C++ share the same myclass object with
    # the Python side.
    self.assertEqual(myclass.get_pod_ptr().get_x(), 10000)

  def testNonConstPointerUncopyableReturn(self):
    myclass = const_pointer_return.MyClass2(100)
    # Test "T *" as a return type, where T is an uncopyable and unmovable class.
    self.assertEqual(const_pointer_return.NoCopy, type(myclass.get_no_copy()))
    self.assertEqual(myclass.get_no_copy().get_x(), 100)
    myclass.get_no_copy().set_x(10000)
    self.assertEqual(myclass.get_no_copy().get_x(), 10000)


if __name__ == '__main__':
  absltest.main()
