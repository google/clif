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

  def testPlain(self):
    num = non_raising.MakeTestNonRaisingPlain()
    self.assertEqual(num, 1)

  def testMarked(self):
    num = non_raising.MakeTestNonRaisingMarked()
    self.assertEqual(num, -1)


if __name__ == '__main__':
  absltest.main()
