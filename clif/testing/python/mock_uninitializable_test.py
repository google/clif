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

from unittest import mock

from absl.testing import absltest
# import pytype_extensions

from clif.python import instrumentation_for_testing as i4t
from clif.testing.python import mock_uninitializable as tm

# assert_type = pytype_extensions.assert_type

# tm.NoCtor is this PyCLIF-wrapped C++ type:
#
#     struct NoCtor {
#       NoCtor() = delete;
#       int Mul100(int i) const { return i * 100; }
#     };
#
# It cannot be initialized from Python. NoCtor here is contrived, but there are
# sound design choices leading to this situation.


class PseudoModule:  # To make this similar to the extension situation.

  class NativeNoCtor:

    def __init__(self):
      raise RuntimeError("Meant to be inaccessible")

    def Mul100(self, i):
      return i * 100

  class NativeWithCtor:

    def __init__(self, state):
      self.state = state

    def Mul100(self, i):
      return self.state * i * 100


class MockUninitializableTest(absltest.TestCase):

  def testMockNativeNoCtor(self):
    with mock.patch.object(PseudoModule, "NativeNoCtor", autospec=True):
      PseudoModule.NativeNoCtor.return_value.Mul100.return_value = (
          300  # pytype: disable=attribute-error
      )
      obj = PseudoModule.NativeNoCtor()
      self.assertEqual(obj.Mul100(2), 300)
      with self.assertRaises(TypeError):
        # pytype: disable=wrong-arg-count
        obj.Mul100(2, 3)  # pylint: disable=too-many-function-args
        # pytype: enable=wrong-arg-count

  def testMockExtensionNoCtor(self):
    with mock.patch.object(tm, "NoCtor", autospec=True):
      tm.NoCtor.return_value.Mul100.return_value = (
          300  # pytype: disable=attribute-error
      )
      obj = tm.NoCtor()
      self.assertEqual(obj.Mul100(2), 300)
      # UNFORTUNATELY no TypeError from mock here,
      #               pylint also fails to detect this, but
      # FORTUNATELY pytype does (without the directives):
      # pytype: disable=wrong-arg-count
      self.assertEqual(obj.Mul100(2, 3), 300)  # too many positional arguments
      # pytype: enable=wrong-arg-count


class FakeExtensionNoCtor(i4t.ProductionType[tm.NoCtor]):

  def __init__(self, state):
    self.state = state
    self.call_count = 0

  def Mul100(self, i):
    self.call_count += 1
    return self.state * i * 100


# When access to instrumented_type is not needed.
@i4t.SealAsProductionType(tm.NoCtor)
class FakeExtensionNoCtorSealedAs:

  def __init__(self):
    self.state = 3

  def Mul100(self, i):
    return self.state * i * 102


# When access to instrumented_type is needed and the fake __init__ signature is
# DIFFERENT from that of production_type.
class FakeExtensionNoCtorInitWithArgsUnsealed(i4t.ProductionType[tm.NoCtor]):

  def __init__(self, state):
    self.state = state

  def Mul100(self, i):
    return self.state * i * 103


# When access to instrumented_type is needed and the fake __init__ signature is
# IDENTICAL to that of production_type (or __init__ has no arguments if
# production_type has no __init__).
class FakeExtensionNoCtorDefaultInitUnsealed(i4t.ProductionType[tm.NoCtor]):

  # __init__ is intentionally missing.

  def Mul100(self, i):
    return i * 104


FakeExtensionNoCtorDefaultInitSealed = (
    FakeExtensionNoCtorDefaultInitUnsealed.SealType()
)


# Very similar to FakeExtensionNoCtorDefaultInitUnsealed, but with
# explicit __init__.
class FakeExtensionNoCtorInitNoArgsUnsealed(i4t.ProductionType[tm.NoCtor]):

  def __init__(self):
    self.state = 8

  def Mul100(self, i):
    return self.state * i * 105


FakeExtensionNoCtorInitNoArgsSealed = (
    FakeExtensionNoCtorInitNoArgsUnsealed.SealType()
)


def ProductionCodePassNoCtor(obj: tm.NoCtor):
  return obj.Mul100(2)


class FakeNativeWithCtor(
    PseudoModule.NativeWithCtor, i4t.ProductionType[PseudoModule.NativeWithCtor]
):

  def __init__(self):  # pylint: disable=super-init-not-called
    # Assume state is difficult to generate via the normal __init__, which is
    # therefore intentionally not called from here.
    self.state = 5


def ProductionCodePassNativeWithCtor(obj: PseudoModule.NativeWithCtor):
  return obj.Mul100(7)


class FakeUninitializableTest(absltest.TestCase):

  def testFakeExtensionNoCtor(self):
    orig_fake_obj = FakeExtensionNoCtor(3)
    obj = orig_fake_obj.Seal()
    # assert_type(obj, tm.NoCtor)
    for expected_call_count in (1, 2):
      self.assertEqual(ProductionCodePassNoCtor(obj), 600)
      fake_obj = i4t.Unseal(obj, FakeExtensionNoCtor)
      assert fake_obj is orig_fake_obj
      # assert_type(fake_obj, FakeExtensionNoCtor)
      self.assertEqual(fake_obj.call_count, expected_call_count)

  def testFakeExtensionNoCtorSealedAs(self):
    obj = FakeExtensionNoCtorSealedAs()
    # assert_type(obj, tm.NoCtor)
    self.assertEqual(ProductionCodePassNoCtor(obj), 612)

  def testFakeExtensionNoCtorInitWithArgs(self):
    obj = FakeExtensionNoCtorInitWithArgsUnsealed(5).Seal()
    # assert_type(obj, tm.NoCtor)
    self.assertEqual(ProductionCodePassNoCtor(obj), 1030)
    fake_obj = i4t.Unseal(obj, FakeExtensionNoCtorInitWithArgsUnsealed)
    # assert_type(fake_obj, FakeExtensionNoCtorInitWithArgsUnsealed)
    self.assertEqual(fake_obj.state, 5)

  def testFakeExtensionNoCtorDefaultInit(self):
    obj = FakeExtensionNoCtorDefaultInitSealed()
    # assert_type(obj, tm.NoCtor)
    self.assertEqual(ProductionCodePassNoCtor(obj), 208)
    fake_obj = i4t.Unseal(obj, FakeExtensionNoCtorDefaultInitUnsealed)
    # assert_type(fake_obj, FakeExtensionNoCtorDefaultInitUnsealed)

  def testFakeExtensionNoCtorInitNoArgs(self):
    obj = FakeExtensionNoCtorInitNoArgsSealed()
    # assert_type(obj, tm.NoCtor)
    self.assertEqual(ProductionCodePassNoCtor(obj), 1680)
    fake_obj = i4t.Unseal(obj, FakeExtensionNoCtorInitNoArgsUnsealed)
    # assert_type(fake_obj, FakeExtensionNoCtorInitNoArgsUnsealed)
    self.assertEqual(fake_obj.state, 8)

  def testFakeNativeWithCtor(self):
    orig_fake_obj = FakeNativeWithCtor()
    obj = orig_fake_obj.Seal()
    # assert_type(obj, PseudoModule.NativeWithCtor)
    self.assertEqual(ProductionCodePassNativeWithCtor(obj), 3500)
    fake_obj = i4t.Unseal(obj, FakeNativeWithCtor)
    assert fake_obj is orig_fake_obj
    # assert_type(fake_obj, FakeNativeWithCtor)


if __name__ == "__main__":
  absltest.main()
