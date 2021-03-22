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

"""Tests for clif.testing.python.t2."""

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import t2
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import t2_pybind11
except ImportError:
  t2_pybind11 = None
# pylint: enable=g-import-not-at-top


class PyK(t2.Klass):
  pass


# This is intentionally old-style. pylint: disable=old-style-class
class OldStyleClass:
  pass


@parameterized.named_parameters([
    np for np in zip(('c_api', 'pybind11'), (t2, t2_pybind11))
    if np[1] is not None
])
class T2Test(absltest.TestCase):

  # This test works as expected when the "user error" in .clif is fixed.
  # def testExplicitConstructor(self, wrapper_lib):
  #   self.assertEqual(t2.NoDefaultConstructor(1).a, 1)

  def testContextManager(self, wrapper_lib):
    self.assertEqual(wrapper_lib.CtxMgr().state,
                     wrapper_lib.CtxMgr.State.UNDEFINED)
    with wrapper_lib.CtxMgr() as c:
      self.assertIsNotNone(c)
      self.assertEqual(c.state, c.State.LOCKED)
    self.assertEqual(c.state, c.State.UNLOCKED)
    with self.assertRaises(ValueError):
      with wrapper_lib.CtxMgr():
        raise ValueError()

  def testVectorUniq(self, wrapper_lib):
    self.assertEqual(wrapper_lib.vector_inside_unique_ptr(), [])
    vs = wrapper_lib.all_nocopy_holds()
    self.assertLen(vs, 3)
    for actual, expected in zip(vs, [1, 2, 3]):
      self.assertIsInstance(actual, wrapper_lib.NoCopy)
      self.assertEqual(actual.a, expected)

  def testVarGetSet(self, wrapper_lib):
    n = wrapper_lib.Nested()
    i = n.get_i()
    i.a = 3
    n.set_i(i)
    self.assertEqual(n.get_i().a, 3)
    # Mutating an object returned by get_i does nothing as it's only a copy.
    n.get_i().a += 1
    self.assertEqual(n.get_i().a, 3)

  def test_setting_nested_container_attribute_persists(self, wrapper_lib):
    nca = wrapper_lib.NestedContainerAttributes()
    nca.int_set_vector = [{1}, {2}, {3}]
    self.assertEqual(nca.int_set_vector, [{1}, {2}, {3}])

  def test_setting_nested_container_attribute_overwrites(self, wrapper_lib):
    nca = wrapper_lib.NestedContainerAttributes()
    nca.int_set_vector = [{1}, {2}, {3}]
    nca.int_set_vector = [{4}]
    self.assertEqual(nca.int_set_vector, [{4}])

  def test_mutating_nested_container_attribute_does_not_persist(
      self, wrapper_lib):
    nca = wrapper_lib.NestedContainerAttributes()
    nca.int_set_vector.append({1})
    self.assertEqual(nca.int_set_vector, [])

  def test_class_name(self, wrapper_lib):
    with self.assertRaisesRegexp(TypeError, r'\bOldStyleClass\b'):
      wrapper_lib.k_check(OldStyleClass())

  def testReturnNoDefaultConstructor(self, wrapper_lib):
    self.assertIsInstance(
        wrapper_lib.make_ndefctor(1), wrapper_lib.NoDefaultConstructor)

  def testMovableButUncopyableClass(self, wrapper_lib):
    self.assertEqual(wrapper_lib.func_return_movable_but_uncopyable_type().a,
                     100)

  def testMovableButUncopyableOutputParameter(self, wrapper_lib):
    output_param = wrapper_lib.OutputParameter()
    movable_return = output_param.MovableButUncopyableOutputParameter1()
    self.assertEqual(movable_return.a, 100)
    movable_return = output_param.MovableButUncopyableOutputParameter2()
    self.assertEqual(movable_return.a, 1)

  def testPassListAsVectorOfNoDefaultConstructor(self, wrapper_lib):
    res0 = wrapper_lib.pass_list_as_vector_of_no_default_constructor([])
    self.assertEqual(res0, 13)
    res3 = wrapper_lib.pass_list_as_vector_of_no_default_constructor(
        [wrapper_lib.make_ndefctor(i) for i in [3, -5, 7]])
    self.assertEqual(res3, 18)


if __name__ == '__main__':
  absltest.main()
