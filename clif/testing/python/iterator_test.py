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

"""Tests for clif.testing.python.iterator."""

import weakref

from absl.testing import absltest

from clif.testing.python import iterator


class IteratorTest(absltest.TestCase):

  def testR5(self):
    r = iterator.Ring5()
    self.assertFalse(r)
    with self.assertRaises(RuntimeError):
      r.pop()
    r.push(1)
    self.assertTrue(r)
    r.push(2)
    self.assertEqual(list(r), [1, 2])
    self.assertEqual(r.pop(), 1)
    r.push(3)
    r.push(4)
    r.push(5)
    r.push(6)
    with self.assertRaises(RuntimeError):
      r.push(7)
    self.assertEqual(r.pop(), 2)  # list() fails without pop() !? :(
    self.assertEqual(list(r), [3, 4, 5, 6])
    r.clear()
    self.assertFalse(r)

  def test_weakref(self):
    r = iterator.Ring5()
    self.assertIsNotNone(weakref.ref(r)())
    with self.assertRaises(TypeError) as ctx:
      weakref.ref(iter(r))
    self.assertIn('cannot create weak reference', str(ctx.exception))


if __name__ == '__main__':
  absltest.main()
