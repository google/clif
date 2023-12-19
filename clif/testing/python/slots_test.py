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

"""Tests for clif.testing.python.slots."""

from absl.testing import absltest

from clif.testing.python import slots


def expected_exception():
  return (
      AttributeError
      if slots.__pyclif_codegen_mode__ == 'pybind11'
      else NotImplementedError
  )


class SlotsTest(absltest.TestCase):

  def testObjectMethods(self):
    a = slots.I5()
    self.assertEqual(hash(a), 0)

  def testRO(self):
    a = slots.I5()
    self.assertLen(a, 5)
    self.assertEqual(list(a), [0]*5)
    a[1] = 1
    self.assertEqual(a[1], 1)
    self.assertEqual(list(a), [0, 1, 0, 0, 0])
    with self.assertRaises(expected_exception()):
      del a[1]

  def testRW(self):
    a = slots.Z5()
    self.assertLen(a, 5)
    self.assertEqual(list(a), [0]*5)
    a[1] = 1
    self.assertEqual(a[1], 1)
    self.assertEqual(list(a), [0, 1, 0, 0, 0])
    del a[1]
    self.assertEqual(list(a), [0]*5)

  def testHashSmallInt(self):
    a = slots.I5()
    a[2] = 3
    a[4] = 5
    self.assertEqual(hash(a), 8)

  def testHashSsizetOverflow(self):
    a = slots.I5()
    a[0] = 999
    self.assertNotEqual(hash(a), 999)

  def testUnHashable(self):
    a = slots.Z5()
    with self.assertRaises(TypeError) as ctx:
      hash(a)
    self.assertIn(' int', str(ctx.exception))


if __name__ == '__main__':
  absltest.main()
