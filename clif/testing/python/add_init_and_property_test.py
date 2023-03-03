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

from clif.testing.python import add_init_and_property as mut


class AddInitAndPropertyTest(absltest.TestCase):

  def testAddInitReturnsOwningSharedPtr(self):
    fh = mut.FieldHolder.Default()
    f = fh.fld
    self.assertEqual(f.wrapped_int, 200)


if __name__ == "__main__":
  absltest.main()
