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

"""Tests for clif.testing.python.nested_fields."""

import unittest
from clif.testing.python import nested_fields


class NestedFieldsTest(unittest.TestCase):

  def testNestedStructFields(self):
    a = nested_fields.AA()
    a.b.c.i = 123
    # The above change was "in-place".
    self.assertEqual(a.b.c.i, 123)

    c = a.b.c
    c.i = 321
    # |c| refers to the "in-place" attribute inside of |a|. Hence, the above
    # change stays.
    self.assertEqual(a.b.c.i, 321)

    del c
    # |a| is still alive and valid
    self.assertEqual(a.b.c.i, 321)

    c = a.b.c
    del a
    # |c| is still alive and valid
    self.assertEqual(c.i, 321)

    a = nested_fields.AA()
    a.b.c.i = 123
    c = a.b.c
    with self.assertRaises(ValueError):
      # Cannot give up |a| as |c| still is alive
      nested_fields.ConsumeAA(a)
    del c
    # Since |c| is now gone, we can give up |a|
    nested_fields.ConsumeAA(a)

    a = nested_fields.AA()
    a.b.c.i = 123
    c = a.b.c
    with self.assertRaises(ValueError):
      # Cannot give up |c|
      nested_fields.ConsumeCC(c)
    del a
    with self.assertRaises(ValueError):
      # Cannot give up |c| even after |a| is gone; |c| holds a part of |a| and
      # is unsafe to give up!
      nested_fields.ConsumeCC(c)

  def testNestedProperties(self):
    # Properties and unproperties call functions which return the field values.
    # We copy the returned values and do not modidy in-place (infact,
    # "in-place" does not have any meaning for such cases.)
    c = nested_fields.CC()
    c.i = 123
    a = nested_fields.AA()
    a.SetC(c)
    c = a.GetC()
    c.i = 321
    # Modifying the above |c| did not modify the field in |a|.
    self.assertEqual(a.GetC().i, 123)

    d = nested_fields.DD()
    d.i = 123
    b = a.b
    b.d = d
    b.d.i = 321
    # Modifying |d| above did not modify the field in |b|.
    self.assertEqual(b.d.i, 123)

  def testNestedContainers(self):
    a = nested_fields.AA()
    a.v.append(123)
    # Above modification of field |v| in |a| did not happen in place.
    self.assertEqual(len(a.v), 0)


if __name__ == '__main__':
  unittest.main()
