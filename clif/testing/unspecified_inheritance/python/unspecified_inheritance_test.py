# Copyright 2023 Google LLC
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

from clif.testing.unspecified_inheritance.python import unspec_base
from clif.testing.unspecified_inheritance.python import unspec_derived


class InheritanceCorrectnessTest(absltest.TestCase):

  def testIt(self):
    sd = unspec_derived.UnspecDerived()
    self.assertEqual(unspec_base.PassUnspecBase(sd), 230)


if __name__ == '__main__':
  absltest.main()
