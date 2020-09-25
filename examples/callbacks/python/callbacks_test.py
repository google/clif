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

"""Tests for clif.examples.callbacks.python.callback."""

import unittest
from callbacks.python import callbacks


def MyGetCallback(data):
  return data.d


def MySetCallback(data):
  data.d = 54321


class CallbackTest(unittest.TestCase):

  def testCallbacks(self):
    d = callbacks.Data()
    d.d = 12345

    # Calling the wrapped function 'Get' with the Python function
    # 'MyGetCallback' as the callback argument.
    self.assertEqual(callbacks.Get(d, MyGetCallback), 12345)

    # Calling the wrapped function 'Set' with the Python function
    # 'MySetCallback' as the callback argument.
    callbacks.Set(MySetCallback, d)
    self.assertEqual(d.d, 54321)

    # Calling the wrapped function 'GetCallback' which returns a callable
    # object.
    callback = callbacks.GetCallback()
    self.assertEqual(callback(i=10, d=d), 54331)


if __name__ == '__main__':
  unittest.main()
