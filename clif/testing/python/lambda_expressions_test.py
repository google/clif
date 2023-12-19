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
from absl.testing import parameterized

from clif.testing.python import lambda_expressions


class CtorTakesAbstractVirtual(lambda_expressions.CtorTakesAbstractVirtual):

  def get(self):
    return self.value + 1


class LambdaExpressionsTest(parameterized.TestCase):

  def test_abstract_reference_parameter(self):
    obj = lambda_expressions.Derived(100)
    self.assertEqual(
        lambda_expressions.abstract_reference_param(obj), b'abstract_reference')

  def test_abstract_pointer_parameter(self):
    obj = lambda_expressions.Derived(10)
    self.assertEqual(
        lambda_expressions.abstract_pointer_param(obj), b'abstract_pointer')

  def test_nomove_reference_parameter(self):
    obj = lambda_expressions.NoCopyNoMove()
    self.assertEqual(lambda_expressions.nocopy_nomove_reference_param(obj),
                     b'nocopy_nomove_reference')

  def test_nomove_pointer_parameter(self):
    obj = lambda_expressions.NoCopyNoMove()
    self.assertEqual(lambda_expressions.nocopy_nomove_pointer_param(obj),
                     b'nocopy_nomove_pointer')

  def test_unique_pointer_parameter(self):
    obj = lambda_expressions.Derived(10)
    self.assertEqual(lambda_expressions.unique_pointer_param(obj),
                     b'unique_ptr')

  def test_ctor_unknown_default_parameter(self):
    obj = lambda_expressions.TestCtor()
    self.assertEqual(obj.value, 10)

  def test_extend_ctor_unknown_default_parameter(self):
    obj = lambda_expressions.TestExtendCtor(10)
    self.assertEqual(obj.value, 110)

  def test_no_default_ctor_return(self):
    obj = lambda_expressions.no_default_ctor_return(100)[0]
    self.assertEqual(obj.get(), 100)

  def test_multiple_returns_with_unique_ptr(self):
    obj = lambda_expressions.multiple_returns_with_unique_ptr()[0]
    self.assertEqual(obj.get(), 10)

  def test_multiple_returns_with_nocopy_object(self):
    obj = lambda_expressions.multiple_returns_with_nocopy_object()[0]
    self.assertEqual(obj.get(), '20')

  def test_ctor_takes_pyobject(self):
    obj = lambda_expressions.CtorTakesPyObj(1000)
    self.assertEqual(obj.value, 1000)
    obj = lambda_expressions.CtorTakesPyObj('123')
    self.assertEqual(obj.value, -1)

  def test_extended_ctor_takes_pyobject(self):
    obj = lambda_expressions.ExtendedCtorTakesPyObj(1001)
    self.assertEqual(obj.value, 1001)
    obj = lambda_expressions.ExtendedCtorTakesPyObj('123')
    self.assertEqual(obj.value, -1)

  def test_ctor_takes_abstract(self):
    derived = lambda_expressions.Derived(10)
    obj = lambda_expressions.CtorTakesAbstract(derived)
    self.assertEqual(obj.value, 10)
    obj = CtorTakesAbstractVirtual(derived)
    self.assertEqual(obj.get(), 11)

  def test_from_nocopy(self):
    nc = lambda_expressions.NoCopy('30')
    self.assertEqual(nc.get(), '30')
    obj = lambda_expressions.FromNoCopy.from_no_copy(nc)
    self.assertEqual(obj.get(), '30')

  def test_generate_operator_with_high_priority(self):
    v1 = lambda_expressions.Derived(10)
    v2 = lambda_expressions.Derived(20)
    self.assertEqual(v1, v1)
    self.assertNotEqual(v1, v2)

  def test_no_reserved_keyword_for_variables(self):
    self.assertEqual(lambda_expressions.returns_one(123), b'1')

  def test_takes_uncopyable_object(self):
    d = lambda_expressions.Derived(1)
    self.assertEqual(lambda_expressions.takes_unique_ptr_vector([d]), b'1')

  def test_nocopy_nomove_object_add_init(self):
    obj = lambda_expressions.NoCopyNoMove.from_value(10)
    self.assertEqual(obj.value, 10)

  def test_gil_acquired_function_accept_iterable_as_vector(self):
    l = [1, 2, 3]
    iterable = (i for i in l)
    self.assertEqual(lambda_expressions.consume_pyobject(l), 3)
    self.assertEqual(lambda_expressions.consume_pyobject(iterable), 3)

  def test_context_manager(self):
    with lambda_expressions.TestCtxMgr() as obj:
      self.assertEqual(obj.value, 20)
    with lambda_expressions.TestExtendCtxMgr() as obj:
      self.assertEqual(obj.value, 10)

  def test_cpp_function_set_python_exception(self):
    expected_exception_type = (
        ValueError if lambda_expressions.__pyclif_codegen_mode__ == 'pybind11'
        else SystemError)
    with self.assertRaises(expected_exception_type):
      lambda_expressions.python_exception_in_function()


@parameterized.parameters(
    ([1, 2, 3],),
    (set([1, 2, 3]),),
)
class AcceptIterableTest(parameterized.TestCase):

  def test_accept_iterable_as_vector(self, iterable):
    self.assertEqual(lambda_expressions.takes_vector(iterable), 3)
    self.assertEqual(lambda_expressions.takes_vector((i for i in iterable)), 3)

  def test_ctor_accept_iterable_as_vector(self, iterable):
    obj = lambda_expressions.CtorTakesVector(iterable)
    self.assertCountEqual(iterable, obj.value)
    obj = lambda_expressions.CtorTakesVector((i for i in iterable))
    self.assertCountEqual(iterable, obj.value)

  def test_extended_ctor_accept_iterable_as_vector(self, iterable):
    obj = lambda_expressions.ExtendedCtorTakesVector(iterable)
    self.assertCountEqual(iterable, obj.value)
    obj = lambda_expressions.ExtendedCtorTakesVector((i for i in iterable))
    self.assertCountEqual(iterable, obj.value)

  def test_accept_iterable_as_set(self, iterable):
    # Explicit set() added with cl/536221955.
    self.assertEqual(lambda_expressions.takes_set(set(iterable)), 3)
    self.assertEqual(lambda_expressions.takes_unordered_set(set(iterable)), 3)
    self.assertEqual(lambda_expressions.takes_set(set(i for i in iterable)), 3)
    self.assertEqual(
        lambda_expressions.takes_unordered_set(set(i for i in iterable)), 3
    )

  def test_ctor_accept_iterable_as_set(self, iterable):
    # Explicit set() added with cl/536221955.
    obj = lambda_expressions.CtorTakesSet(set(iterable))
    self.assertCountEqual(iterable, obj.value)
    obj = lambda_expressions.CtorTakesUnorderedSet(set(iterable))
    self.assertCountEqual(iterable, obj.value)
    obj = lambda_expressions.CtorTakesSet(set(i for i in iterable))
    self.assertCountEqual(iterable, obj.value)
    obj = lambda_expressions.CtorTakesUnorderedSet(set(i for i in iterable))
    self.assertCountEqual(iterable, obj.value)

  def test_extended_ctor_accept_iterable_as_set(self, iterable):
    # Explicit set() added with cl/536221955.
    obj = lambda_expressions.ExtendedCtorTakesSet(set(iterable))
    self.assertCountEqual(iterable, obj.value)
    obj = lambda_expressions.ExtendedCtorTakesUnorderedSet(set(iterable))
    self.assertCountEqual(iterable, obj.value)
    obj = lambda_expressions.ExtendedCtorTakesSet(set(i for i in iterable))
    self.assertCountEqual(iterable, obj.value)
    obj = lambda_expressions.ExtendedCtorTakesUnorderedSet(
        set(i for i in iterable)
    )
    self.assertCountEqual(iterable, obj.value)


if __name__ == '__main__':
  absltest.main()
