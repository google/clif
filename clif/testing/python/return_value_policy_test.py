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

from clif.testing.python import return_value_policy


class ReturnValuePolicyTestCase(parameterized.TestCase):

  @parameterized.parameters(
      ('return_value', '^return_value_MvCtor(_MvCtor)*$'),
      ('return_reference', r'^return_reference(_CpCtor)*(_MvCtor)*$'),
      ('return_const_reference', '^return_const_reference_CpCtor(_MvCtor)*$'),
      ('return_pointer', '^return_pointer$'),
      ('return_value_policy_copy', '^return_pointer(_CpCtor)*$'),
      ('return_value_policy_move', '^return_pointer(_MvCtor)*$'),
      ('return_value_policy_reference', '^return_pointer$'),
      ('return_value_policy_take_ownership', '^return_pointer_unowned$'),
      ('return_value_policy_automatic', '^return_pointer_unowned$'),
      ('return_const_pointer', '^return_const_pointer_CpCtor$'),
      ('return_shared_pointer', '^return_shared_pointer$'),
      ('return_unique_pointer', '^return_unique_pointer$'),
      ('return_value_nocopy', '^return_value_nocopy_MvCtor(_MvCtor)*$'),
      ('return_reference_nocopy', '^return_reference_nocopy_MvCtor$'),
      ('return_pointer_nocopy', '^return_pointer_nocopy$'),
      ('return_shared_pointer_nocopy', '^return_shared_pointer_nocopy$'),
      ('return_unique_pointer_nocopy', '^return_unique_pointer_nocopy$'),
      ('return_value_nomove', '^return_value_nomove_CpCtor(_CpCtor)*$'),
      ('return_reference_nomove', '^return_reference_nomove_CpCtor(_CpCtor)*$'),
      ('return_pointer_nomove', '^return_pointer_nomove$'),
      ('return_const_reference_nomove',
       '^return_const_reference_nomove_CpCtor(_CpCtor)*$'),
      ('return_const_pointer_nomove', '^return_const_pointer_nomove_CpCtor$'),
      ('return_shared_pointer_nomove', '^return_shared_pointer_nomove$'),
      ('return_unique_pointer_nomove', '^return_unique_pointer_nomove$'),
      ('return_pointer_nocopy_nomove', '^return_pointer_nocopy_nomove$'),
      ('return_shared_pointer_nocopy_nomove',
       '^return_shared_pointer_nocopy_nomove$'),
      ('return_unique_pointer_nocopy_nomove',
       '^return_unique_pointer_nocopy_nomove$')
  )
  def testReturnValue(self, return_function, expected):
    ret = getattr(return_value_policy, return_function)()
    self.assertRegex(ret.mtxt, expected)

  @absltest.skipIf(
      'pybind11' not in return_value_policy.__doc__,
      'Legacy PyCLIF does not use return value policy')
  def testReturnAsBytes(self):
    ret = return_value_policy.return_string()
    self.assertEqual(ret, b'return_string')


if __name__ == '__main__':
  absltest.main()
