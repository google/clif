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

"""Tests for clif.examples.wrap_protos.python.wrap_protos."""

import unittest
import wrap_protos
import sample_pb2


class WrapProtosTest(unittest.TestCase):

  def testProtos(self):
    s = sample_pb2.MyMessage()
    # Even though DefaultInitSample on the C++ side takes a pointer to the
    # proto, |s| is serialized and deserialized in to a copy of the C++ proto.
    # Hence, changes made to the proto on the C++ side do not reflect in Python.
    wrap_protos.DefaultInitMyMessage(s)
    self.assertNotEqual(s.name, 'default')

    # |s| is a normal Python proto with all its normal Python proto API.
    s.name = 'my_python_name'
    s.msg.id.append(123)
    s.msg.id.append(345)
    self.assertEqual(len(s.msg.id), 2)

    pman = wrap_protos.ProtoManager()

    # The GetSample method returns a copy of the proto even though the C++
    # method returns a pointer. The C++ proto is serialized and then
    # deserialized into a Python proto.
    s = pman.GetMyMessage()
    self.assertEqual(s.name, 'default')
    # Changing the proto in Python does not have any effect on the C++ side.
    s.name = 'new_name'
    s = pman.GetMyMessage()
    self.assertEqual(s.name, 'default')

    # Create instances of nested proto messages using the '.' notation as usual.
    nested = sample_pb2.MyMessage.Nested()
    nested.value = sample_pb2.MyMessage.Nested.DEFAULT
    # And pass them to a wrapped functions as usual.
    msg = wrap_protos.MakeMyMessageFromNested(nested)
    self.assertEquals(msg.name, 'from_nested')

    enum_val = sample_pb2.MyMessage.Nested.EXPLICIT
    msg = wrap_protos.MakeMyMessageFromNestedEnum(enum_val)
    self.assertEquals(msg.name, 'from_nested_enum')


if __name__ == '__main__':
  unittest.main()
