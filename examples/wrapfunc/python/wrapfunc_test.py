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

"""Tests for clif.examples.wrapfunc.python.wrapfunc."""

import unittest
import wrapfunc
import wrappod


class WrapfuncTest(unittest.TestCase):

  def testFuncs(self):
    wrapfunc.ResetState()

    wrapfunc.SetState(123)
    self.assertEqual(wrapfunc.GetState(), 123)

    wrapfunc.SetStateFromSum(1230, 4)
    self.assertEqual(wrapfunc.GetState(), 1234)

    s = wrappod.MyClass()
    s.a = 1000
    before = s.a
    wrapfunc.SetStateFromMyClass(s)
    self.assertEqual(wrapfunc.GetState(), 1000)

    # The C++ SetStateFromSimple modifies the value parameter.
    # However since it is a value parameter in C++, it should not be visible to
    # the caller. Works as expected.
    self.assertEqual(before, s.a)

    wrapfunc.SetState(123)
    wrapfunc.Store(s)
    self.assertEqual(s.a, 123)

    s1 = wrapfunc.StoreInNew()
    # s1 is a new object.
    self.assertIsNot(s1, s)


if __name__ == '__main__':
  unittest.main()
