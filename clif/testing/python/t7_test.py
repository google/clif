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

"""Tests for clif.testing.python.t7."""

import unittest
from clif.testing.python import t7


class T7Test(unittest.TestCase):

  def testFuncInput(self):
    if str is bytes:  # PY2
      t7.SetCallback(lambda n: str(n+2))
    else:
      # t7.SetCallback(lambda n: b'%d' % (n+2))  # 3.5+
      # until then use that ugly workaround:
      t7.SetCallback(lambda n: str(n+2).encode('ascii'))
    self.assertEqual(t7.settled(), b'3')
    # Following tests raises TypeError during callback and can't be caught here.
    # ifdef FATAL_CALLBACK_EXCEPTION on py_clif_cc rule, log.FATAL aborts.
    # self.assertRaises(TypeError, t7.SetCallback, (1))
    # self.assertRaises(TypeError, t7.SetCallback, lambda: 1)
    # self.assertRaises(TypeError, t7.SetCallback, lambda: '1')
    # self.assertRaises(TypeError, t7.SetCallback, lambda a, b: '1')

  def testFuncOutput(self):
    f = t7.GetF()
    self.assertEqual(f(), 1)
    f = t7.GetF1()
    self.assertEqual(f(True), 1)
    self.assertEqual(f(False), 0)


if __name__ == '__main__':
  unittest.main()
