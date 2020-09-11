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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import unittest

import parameterized

from clif.testing.python import enable_instance_dict

TYPES_WITH_DICT = (
    enable_instance_dict.ConcreteEmptyWithDict,
    enable_instance_dict.ConcreteEmptyWithDictFinal,
    enable_instance_dict.ConcreteNonTrivialDestructorWithDict)


###############################################################################
# NOTE: The sys.getrefcount() tests in this file are highly conclusive if     #
#       they work, but make assumptions about Python's behavior that may      #
#       not necessarily be true in the future. If you see these tests failing #
#       with new versions of Python, they may need to be adjusted.            #
###############################################################################


class ClassModuleAttrTest(unittest.TestCase):

  def testConcreteEmptyNoDict(self):
    obj = enable_instance_dict.ConcreteEmptyNoDict()
    self.assertFalse(hasattr(obj, '__dict__'))

  @parameterized.parameterized.expand(zip(TYPES_WITH_DICT))
  def testConcreteEmptyWithDict(self, type_with_dict):
    obj = type_with_dict()
    self.assertTrue(hasattr(obj, '__dict__'))
    self.assertEqual(len(obj.__dict__), 0)
    obj.color = 'red'
    self.assertEqual(len(obj.__dict__), 1)
    obj.height = '13'
    self.assertEqual(len(obj.__dict__), 2)
    with self.assertRaises(TypeError) as ctx:
      obj.__dict__ = ''
    self.assertEqual(
        str(ctx.exception),
        '__dict__ must be set to a dict, not a str')
    initial_dict = obj.__dict__
    self.assertEqual(sys.getrefcount(initial_dict), 3)
    obj.__dict__ = {'seven': 7, 'ate': 8, 'nine': 9}
    self.assertEqual(sys.getrefcount(initial_dict), 2)
    self.assertEqual(len(obj.__dict__), 3)
    replacement_dict = obj.__dict__
    self.assertEqual(sys.getrefcount(replacement_dict), 3)
    del obj
    self.assertEqual(sys.getrefcount(replacement_dict), 2)

  @parameterized.parameterized.expand(zip(TYPES_WITH_DICT))
  def testReferenceCycle(self, type_with_dict):
    obj = type_with_dict()
    obj.cycle = obj
    obj_dict = obj.__dict__
    self.assertEqual(sys.getrefcount(obj_dict), 3)
    del obj
    self.assertEqual(sys.getrefcount(obj_dict), 3)  # NOT 2
    del obj_dict['cycle']  # breaks the reference cycle
    self.assertEqual(sys.getrefcount(obj_dict), 2)

  def testConcreteEmptyWithDictFinal(self):
    # Minimal runtime testing. The main purpose of ConcreteEmptyWithDictFinal
    # is to test that the .clif file parser can handle multiple decorators.
    with self.assertRaises(TypeError) as ctx:
      class _(enable_instance_dict.ConcreteEmptyWithDictFinal):
        pass
    self.assertIn('is not an acceptable base type', str(ctx.exception))


if __name__ == '__main__':
  unittest.main()
