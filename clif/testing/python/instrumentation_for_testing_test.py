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
import pytype_extensions
from pytype_extensions import instrumentation_for_testing as i4t

from clif.testing.python import mock_uninitializable as tm

assert_type = pytype_extensions.assert_type


class FakeNoCtorInitArgUnsealed(i4t.ProductionType[tm.NoCtor]):

  def __init__(self, state):
    self.state = state
    self.call_count = 0

  def Mul100(self, i):
    self.call_count += 1
    return self.state * i * 100


class FakeNoCtorInitNoArgsUnsealed(i4t.ProductionType[tm.NoCtor]):

  def __init__(self):
    self.call_count = 0

  def Mul100(self, i):
    self.call_count += 1
    return i * 104


FakeNoCtorInitNoArgsSealed = FakeNoCtorInitNoArgsUnsealed.SealType()


@i4t.SealAsProductionType(tm.NoCtor)
class FakeNoCtorSealedAs:

  def __init__(self):
    self.state = 3

  def Mul100(self, i):
    return self.state * i * 102


def ProductionCodePassNoCtor(obj: tm.NoCtor):
  return obj.Mul100(2)


class FakeUninitializableTest(absltest.TestCase):

  def testFakeNoCtorInitArg(self):
    orig_fake_obj = FakeNoCtorInitArgUnsealed(3)
    obj = orig_fake_obj.Seal()
    assert_type(obj, tm.NoCtor)
    for expected_call_count in (1, 2):
      self.assertEqual(ProductionCodePassNoCtor(obj), 600)
      fake_obj = i4t.Unseal(obj, FakeNoCtorInitArgUnsealed)
      assert fake_obj is orig_fake_obj
      assert_type(fake_obj, FakeNoCtorInitArgUnsealed)
      self.assertEqual(fake_obj.call_count, expected_call_count)

  def testFakeNoCtorInitNoArgs(self):
    obj = FakeNoCtorInitNoArgsSealed()
    assert_type(obj, tm.NoCtor)
    self.assertEqual(ProductionCodePassNoCtor(obj), 208)
    fake_obj = i4t.Unseal(obj, FakeNoCtorInitNoArgsUnsealed)
    assert_type(fake_obj, FakeNoCtorInitNoArgsUnsealed)
    self.assertEqual(fake_obj.call_count, 1)

  def testFakeNoCtorSealedAs(self):
    obj = FakeNoCtorSealedAs()
    assert_type(obj, tm.NoCtor)
    self.assertEqual(ProductionCodePassNoCtor(obj), 612)


if __name__ == "__main__":
  absltest.main()
