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

import sys

from absl.testing import absltest
from absl.testing import parameterized

from clif.testing.python import enable_instance_dict
# TODO: Restore simple import after OSS setup includes pybind11.
# pylint: disable=g-import-not-at-top
try:
  from clif.testing.python import enable_instance_dict_pybind11
except ImportError:
  enable_instance_dict_pybind11 = None
# pylint: enable=g-import-not-at-top

WRAPPER_LIBS = (('c_api', enable_instance_dict),
                ('pybind11', enable_instance_dict_pybind11))

TYPES_WITH_DICT = (
    'ConcreteEmptyWithDict',
    'ConcreteEmptyWithDictFinal',
    'ConcreteNonTrivialDestructorWithDict')


def MakeNamedParameters():
  np = []
  for code_gen, wrapper_lib in WRAPPER_LIBS:
    if wrapper_lib is not None:
      for type_with_dict in TYPES_WITH_DICT:
        np.append(('_'.join((type_with_dict, code_gen)),
                   getattr(wrapper_lib, type_with_dict)))
  return np


###############################################################################
# NOTE: The sys.getrefcount() tests in this file are highly conclusive if     #
#       they work, but make assumptions about Python's behavior that may      #
#       not necessarily be true in the future. If you see these tests failing #
#       with new versions of Python, they may need to be adjusted.            #
###############################################################################


@parameterized.named_parameters(
    [np for np in WRAPPER_LIBS if np[1] is not None])
class ClassModuleAttrTestOneTypeOnly(absltest.TestCase):

  def testConcreteEmptyNoDict(self, wrapper_lib):
    obj = wrapper_lib.ConcreteEmptyNoDict()
    self.assertFalse(hasattr(obj, '__dict__'))

  def testConcreteEmptyWithDictFinal(self, wrapper_lib):
    # Minimal runtime testing. The main purpose of ConcreteEmptyWithDictFinal
    # is to test that the .clif file parser can handle multiple decorators.
    with self.assertRaises(TypeError) as ctx:
      class _(wrapper_lib.ConcreteEmptyWithDictFinal):
        pass
    self.assertIn('is not an acceptable base type', str(ctx.exception))


@parameterized.named_parameters(MakeNamedParameters())
class ClassModuleAttrTestMultipleTypes(absltest.TestCase):

  def testConcreteEmptyWithDict(self, type_with_dict):
    obj = type_with_dict()
    self.assertTrue(hasattr(obj, '__dict__'))
    self.assertEmpty(obj.__dict__)
    obj.color = 'red'
    self.assertLen(obj.__dict__, 1)
    obj.height = '13'
    self.assertLen(obj.__dict__, 2)
    with self.assertRaises(TypeError):
      obj.__dict__ = ''
    initial_dict = obj.__dict__
    self.assertEqual(sys.getrefcount(initial_dict), 3)
    obj.__dict__ = {'seven': 7, 'ate': 8, 'nine': 9}
    self.assertEqual(sys.getrefcount(initial_dict), 2)
    self.assertLen(obj.__dict__, 3)
    replacement_dict = obj.__dict__
    self.assertEqual(sys.getrefcount(replacement_dict), 3)
    del obj
    self.assertEqual(sys.getrefcount(replacement_dict), 2)

  def testReferenceCycle(self, type_with_dict):
    obj = type_with_dict()
    obj.cycle = obj
    obj_dict = obj.__dict__
    self.assertEqual(sys.getrefcount(obj_dict), 3)
    del obj
    self.assertEqual(sys.getrefcount(obj_dict), 3)  # NOT 2
    del obj_dict['cycle']  # breaks the reference cycle
    self.assertEqual(sys.getrefcount(obj_dict), 2)


if __name__ == '__main__':
  absltest.main()
