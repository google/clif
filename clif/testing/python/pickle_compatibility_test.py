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

import base64
import copy
import itertools
import os
import pickle
import subprocess
import unittest
import warnings

import parameterized

from clif.testing.python import extension_type_refcount
from clif.testing.python import pickle_compatibility

TEST_SRCDIR = os.environ.get('TEST_SRCDIR')

# Re-using extension_type_refcount.*Empty types.
EMPTY_TYPES = (
    extension_type_refcount.ConcreteEmpty,
    extension_type_refcount.VirtualDerivedEmpty)

STORE_TYPES = (
    pickle_compatibility.StoreTwoUsingPostproc,
    pickle_compatibility.StoreTwoUsingExtend)


class PickleCompatibilityTest(unittest.TestCase):

  def testAssumptions(self):
    self.assertGreaterEqual(pickle.HIGHEST_PROTOCOL, 0)

  @parameterized.parameterized.expand(range(pickle.HIGHEST_PROTOCOL + 1))
  def testSimpleCallable(self, protocol):
    self.assertEqual(pickle_compatibility.SimpleCallable(), 234)
    serialized = pickle.dumps(
        pickle_compatibility.SimpleCallable, protocol=protocol
    )
    self.assertIn(b'clif.testing.python._pickle_compatibility', serialized)
    self.assertIn(b'SimpleCallable', serialized)
    deserialized = pickle.loads(serialized)
    self.assertEqual(deserialized(), 234)
    self.assertIs(deserialized, pickle_compatibility.SimpleCallable)

  def testSimpleMethod(self):
    obj = pickle_compatibility.SimpleStruct()
    self.assertEqual(obj.SimpleMethod(), -987)
    with self.assertRaisesRegex(
        TypeError, 'missing __getinitargs__ and/or __getstate__'
    ):
      pickle.dumps(obj.SimpleMethod)

  @parameterized.parameterized.expand(zip(EMPTY_TYPES))
  def testUnpicklable(self, empty_type):
    obj = empty_type()
    self.assertIs(empty_type.__reduce__, object.__reduce__)
    self.assertIsNot(empty_type.__reduce_ex__, object.__reduce_ex__)
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
      with self.assertRaisesRegex(
          TypeError,
          "^can't pickle .* object: missing __getinitargs__"
          " and/or __getstate__$"):
        obj.__reduce_ex__(protocol)

  @parameterized.parameterized.expand(itertools.product(
      STORE_TYPES,
      range(pickle.HIGHEST_PROTOCOL + 1)))
  def testStoreTwoMethods(self, store_type, protocol):
    store = store_type(-7, 11)
    self.assertEqual(store.Get(0), -7)
    self.assertEqual(store.Get(1), 11)
    reduced = store.__reduce_ex__(protocol)
    self.assertEqual(len(reduced), 2)
    self.assertSequenceEqual(reduced[1], (-7, 11))

  @parameterized.parameterized.expand(itertools.product(
      STORE_TYPES,
      range(pickle.HIGHEST_PROTOCOL + 1)))
  def testStoreTwoPickleRoundTrip(self, store_type, protocol):
    store = store_type(13, -15)
    serialized = pickle.dumps(store, protocol)
    deserialized = pickle.loads(serialized)
    self.assertEqual(deserialized.Get(0), 13)
    self.assertEqual(deserialized.Get(1), -15)

  def testStoreTwoIGS(self):
    obj = pickle_compatibility.StoreTwoIGS(-38, 27)
    obj.__setstate__('blue')
    cpy = copy.deepcopy(obj)
    self.assertSequenceEqual(cpy.__getinitargs__(), (-38, 27))
    self.assertEqual(cpy.__getstate__(), 'blue')

  def testStoreTwoI(self):
    obj = pickle_compatibility.StoreTwoI(-83, 72)
    obj.SetState('green')
    cpy = copy.deepcopy(obj)
    self.assertSequenceEqual(cpy.__getinitargs__(), (-83, 72))  # state lost.
    self.assertEqual(cpy.GetState(), 'blank')

  def testStoreTwoGS(self):
    obj = pickle_compatibility.StoreTwoGS()
    obj.SetValues(94, 53)
    obj.__setstate__('magenta')
    cpy = copy.deepcopy(obj)
    self.assertSequenceEqual(cpy.GetInitArgs(), (-1, -2))  # values lost.
    self.assertEqual(cpy.__getstate__(), 'magenta')

  def testStoreTwoG(self):
    obj = pickle_compatibility.StoreTwoG()
    with self.assertRaisesRegex(
        TypeError,
        "^can't pickle clif.testing.python"
        "._pickle_compatibility.StoreTwoG object:"
        " has __setstate__ but missing __getstate__$"):
      obj.__reduce_ex__(0)

  def testStoreTwoS(self):
    obj = pickle_compatibility.StoreTwoS()
    with self.assertRaisesRegex(
        TypeError,
        "^can't pickle clif.testing.python"
        "._pickle_compatibility.StoreTwoS object:"
        " has __getstate__ but missing __setstate__$"):
      obj.__reduce_ex__(0)

  def testStoreTwoImixup(self):
    obj = pickle_compatibility.StoreTwoImixup()
    with self.assertRaisesRegex(
        ValueError,
        r'^clif.testing.python'
        r'._pickle_compatibility.StoreTwoImixup.__getinitargs__'
        r' must return a tuple or list \(got str\)$'):
      obj.__reduce_ex__(0)

  # For manual testing:
  #   set limit=None,
  #   run this test,
  #   monitor RES with top command.
  def testForLeaksInInfiniteLoop(self, limit=100):
    all_picklable = []
    all_unpicklable = []
    for cls in EMPTY_TYPES:
      all_unpicklable.append(cls())
    for cls in STORE_TYPES + (pickle_compatibility.StoreTwoIGS,
                              pickle_compatibility.StoreTwoI):
      all_picklable.append(cls(1, 2))
    all_picklable.append(pickle_compatibility.StoreTwoGS())
    for cls in (pickle_compatibility.StoreTwoG,
                pickle_compatibility.StoreTwoS,
                pickle_compatibility.StoreTwoImixup):
      all_unpicklable.append(cls())
    pickle_implementations = [pickle]
    warnings.simplefilter('once')
    for counter in itertools.count():
      if limit is not None and counter >= limit:
        break
      for obj in all_picklable:
        for pickle_impl in pickle_implementations:
          pickle_impl.dumps(obj, pickle.HIGHEST_PROTOCOL)
      for obj in all_unpicklable:
        for pickle_impl in pickle_implementations:
          try:
            pickle_impl.dumps(obj)
          except (TypeError, ValueError):
            pass
          else:
            raise RuntimeError('Exception expected.')

  @unittest.skipIf(
      TEST_SRCDIR is None,
      'unable to locate subtest binary.')
  def testUnpickleSubtest(self):
    # Exercises @extend target_class.__module__ = from_class.__module__
    # in type_customization.py.
    subtest_par_path = os.path.join(
        TEST_SRCDIR,
        'clif/testing/python/'
        'pickle_compatibility_unpickle_subtest_binary.par')
    self.assertTrue(os.path.isfile(subtest_par_path))
    store = pickle_compatibility.StoreTwoUsingExtend(15, -9)
    # The pickle protocol level does not matter for this test.
    serialized = pickle.dumps(store, 0)
    b64blob = base64.b64encode(serialized)  # To maximize robustness.
    subproc = subprocess.Popen(
        (subtest_par_path,),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    sub_out, sub_err = subproc.communicate(input=b64blob)
    self.assertMultiLineEqual(sub_err.decode(), '')
    self.assertMultiLineEqual(
        sub_out.decode(),
        'L=2 N=StoreTwoUsingExtend A=(-9, 15)\n')


if __name__ == '__main__':
  unittest.main()
