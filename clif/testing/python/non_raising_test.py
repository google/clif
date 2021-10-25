# Copyright 2021 Google LLC
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

from clif.testing.python import non_raising


class NonRaisingTest(absltest.TestCase):

  def testReturnTestNonRaisingPlain(self):
    num = non_raising.ReturnTestNonRaisingPlain()
    self.assertEqual(num, 1)

  def testReturnTestNonRaisingMarked(self):
    num = non_raising.ReturnTestNonRaisingMarked()
    self.assertEqual(num, -1)

  def testReturnTestNonRaisingAndIvalPlain(self):
    num, ival = non_raising.ReturnTestNonRaisingAndIvalPlain()
    self.assertEqual(num, 1)
    self.assertEqual(ival, 3)

  def testReturnTestNonRaisingAndIvalMarked(self):
    num, ival = non_raising.ReturnTestNonRaisingAndIvalMarked()
    self.assertEqual(num, -1)
    self.assertEqual(ival, 3)

  def testReturnIvalAndTestNonRaisingPlain(self):
    ival, num = non_raising.ReturnIvalAndTestNonRaisingPlain()
    self.assertEqual(ival, 5)
    self.assertEqual(num, 1)

  def testReturnIvalAndTestNonRaisingMarked(self):
    ival, num = non_raising.ReturnIvalAndTestNonRaisingMarked()
    self.assertEqual(ival, 5)
    self.assertEqual(num, -1)


if __name__ == '__main__':
  absltest.main()
