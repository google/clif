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

"""Tests for clif.testing.python.t3."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import t3
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import t3_pybind11
except ImportError:
  t3_pybind11 = None
# pylint: enable=g-import-not-at-top


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (t3, t3_pybind11))
    if np[1] is not None
])
class T3Test(absltest.TestCase):

  def testEnum(self, wrapper_lib):
    w = wrapper_lib
    self.assertEqual(w._Old.TOP1, 1)
    self.assertEqual(w._Old.TOPn, -1)
    self.assertNotEqual(w._New.TOP, 1)
    self.assertEqual(w._New.TOP.name, 'TOP')
    self.assertTrue(w._New.BOTTOM)
    self.assertEqual(w._New.BOTTOM, w._New(1))
    self.assertEqual(w._New.TOP, w._New(1000))
    self.assertEqual(w.K.OldE.ONE, 1)
    self.assertEqual(w.K.NewE.ONE, w.K.NewE(11))
    self.assertRaises(TypeError, w.K().M, (5))
    # This is necessary for proper pickling.
    self.assertEqual(w._New.__module__, w.__name__)


if __name__ == '__main__':
  absltest.main()
