# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://wwt3.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for clif.testing.python.t3."""

import pickle
import sys

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import t3


class T3Test(parameterized.TestCase):

  def testEnumBasic(self):
    self.assertEqual(t3._Old.TOP1, 1)
    self.assertEqual(t3._Old.TOPn, -1)
    self.assertNotEqual(t3._New.TOP, 1)
    self.assertEqual(t3._New.TOP.name, 'TOP')
    self.assertTrue(t3._New.BOTTOM)
    self.assertEqual(t3._New.BOTTOM, t3._New(1))
    self.assertEqual(t3._New.TOP, t3._New(1000))
    self.assertEqual(t3.K.OldE.ONE, 1)
    self.assertEqual(t3.K.NewE.ONE, t3.K.NewE(11))
    self.assertRaises(TypeError, t3.K().M, (5))

  def testEnumModuleName(self):
    # This is necessary for proper pickling.
    self.assertEqual(t3._Old.__module__, t3.__name__)
    self.assertEqual(t3._New.__module__, t3.__name__)

  @parameterized.parameters(
      t3._Old.TOP1, t3._Old.TOPn, t3._New.TOP, t3._New.BOTTOM
  )
  def testPickleRoundtrip(self, orig):
    serialized = pickle.dumps(orig)
    restored = pickle.loads(serialized)
    self.assertEqual(restored, orig)

  def testEnumBases(self):
    old_bases = t3._Old.__bases__
    new_bases = t3._New.__bases__
    # Intentionally avoiding direct import, to not spoil exercising the
    # implicit import in the test itself.
    enum_module = sys.modules.get('enum')
    # Necessary (although not sufficient to prove that the implicit import
    # works).
    self.assertIsNotNone(enum_module)
    self.assertEqual(old_bases, (enum_module.IntEnum,))
    self.assertEqual(new_bases, (enum_module.Enum,))

  def testEnumsExportedToParentScope(self):
    self.assertEqual(t3.Outer.A, t3.Outer.Inner.A)
    self.assertEqual(t3.Outer.B, t3.Outer.Inner.B)

  def testIterateEnum(self):
    l = [e for e in t3._Old]
    self.assertCountEqual(l, [t3._Old.TOP1, t3._Old.TOPn])


if __name__ == '__main__':
  absltest.main()
