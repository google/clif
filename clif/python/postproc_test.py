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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest

import parameterized

from clif.python import postproc


class PostprocTest(unittest.TestCase):

  def testAsTupleOrList(self):
    self.assertTupleEqual(postproc.AsTuple([4, 8, 5]), (4, 8, 5))
    self.assertTupleEqual(postproc.AsSortedTuple('xzy'), ('x', 'y', 'z'))
    self.assertListEqual(postproc.AsList((5.1, 2.6)), [5.1, 2.6])
    self.assertListEqual(postproc.AsSortedList((3, 9, 6)), [3, 6, 9])

  @parameterized.parameterized.expand((
      ('ValueErrorOnFalse', ValueError),
      ('RuntimeErrorOnFalse', RuntimeError),
      ('IgnoreTrueOrFalse', None)))
  def testExceptionType(self, caller_name, error_type):
    postproc_function = getattr(postproc, caller_name)
    for ok in (True,) if error_type is not None else (True, False):
      self.assertIsNone(postproc_function(ok))
      self.assertEqual(postproc_function(ok, 1), 1)
      self.assertEqual(postproc_function(ok, 1, 2), (1, 2))
    for args in ((0,), (0, 1), (0, 1, 2)):
      with self.assertRaises(TypeError) as ctx:
        postproc_function(*args)
      self.assertEqual(
          str(ctx.exception),
          'Use %s only on bool return value' % caller_name)
    if error_type is not None:
      for args in ((False,), (False, 1), (False, 1, 2)):
        with self.assertRaises(error_type) as ctx:
          postproc_function(False)
        self.assertEqual(
            str(ctx.exception),
            'CLIF wrapped call returned False')


if __name__ == '__main__':
  unittest.main()
