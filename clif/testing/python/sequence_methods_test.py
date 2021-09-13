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

from absl.testing import absltest

from clif.testing.python import sequence_methods


class SequenceMethodsTest(absltest.TestCase):

  def testTwoSequence(self):
    s13 = sequence_methods.TwoSequence(1, 3)
    self.assertLen(s13, 2)  # sq_length
    s50 = sequence_methods.TwoSequence(5, 0)
    self.assertLen(s50, 1)
    s00 = sequence_methods.TwoSequence(0, 0)
    self.assertEmpty(s00)
    s51 = s50 + s13  # sq_concat
    self.assertEqual(s51[0], 5)  # sq_item
    self.assertEqual(s51[1], 1)
    s57 = s50 * (-7)  # sq_repeat
    self.assertSequenceEqual((s57[0], s57[1]), (5, -7))

    svv = sequence_methods.TwoSequence(4, 9)
    self.assertSequenceEqual((svv[0], svv[1]), (4, 9))
    svv[1] = 6  # sq_ass_item: setitem
    self.assertSequenceEqual((svv[0], svv[1]), (4, 6))
    del svv[0]  # sq_ass_item: delitem
    self.assertSequenceEqual((svv[0], svv[1]), (0, 6))
    del svv[1]
    self.assertEmpty(svv)

    self.assertIn(5, s57)  # sq_contains
    self.assertIn(-7, s57)
    self.assertNotIn(7, s57)

    svv = sequence_methods.TwoSequence(13, 15)
    svv += s57  # sq_inplace_concat
    self.assertSequenceEqual((svv[0], svv[1]), (13, -7))
    svv = sequence_methods.TwoSequence(17, 19)
    svv *= 11  # sq_inplace_repeat
    self.assertSequenceEqual((svv[0], svv[1]), (17, 11))


if __name__ == '__main__':
  absltest.main()
