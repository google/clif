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

"""Tests for clif.python.slots."""

import textwrap
import unittest
from clif.python import py2slots
from clif.python import py3slots
from clif.python import slots


class SlotsTest(unittest.TestCase):

  def testRichcmp(self):
    code = '\n'.join(
        slots.GenSlots([('__eq__', 'wrap_eq')], {'tp_flags': []}))
    self.assertMultiLineEqual(code, textwrap.dedent("""
        PyObject* slot_richcmp(PyObject* self, PyObject* other, int op) {
          switch (op) {
            case Py_EQ: return slot::adapter<wrap_eq>(self, other);
            default:
              Py_INCREF(Py_NotImplemented);
              return Py_NotImplemented;
          }
        }"""))

  def testDelattr(self):
    code = '\n'.join(
        slots.GenSlots([('__delattr__', 'wrap_da')], {'tp_flags': []}))
    self.assertMultiLineEqual(code, textwrap.dedent("""
        int slot_seto(PyObject* self, PyObject* name, PyObject* value) {
          if (value != nullptr) {
            PyErr_SetNone(PyExc_NotImplementedError);
            return -1;
          } else {
            PyObject* args = PyTuple_Pack(1, name);
            if (args == nullptr) return -1;
            int r = slot::ignore(wrap_da(self, args, nullptr));
            Py_DECREF(args);
            return r;
          }
        }"""))

  def testGetItem(self):
    code = '\n'.join(
        slots.GenSlots([('__getitem__#', 'wrap_get')], {'tp_flags': []}))
    self.assertMultiLineEqual(code, textwrap.dedent("""
        PySequenceMethods AsSequence = {
          nullptr,                             // sq_length
          nullptr,                             // sq_concat
          nullptr,                             // sq_repeat
          slot::getitem<wrap_get>,             // sq_item
          nullptr,                             // sq_slice
          nullptr,                             // sq_ass_item
          nullptr,                             // sq_ass_slice
          nullptr,                             // sq_contains
          nullptr,                             // sq_inplace_concat
          nullptr,                             // sq_inplace_repeat
        };"""))

  def testSetItem(self):
    code = '\n'.join(
        slots.GenSlots([('__setitem__#', 'wrap_get')], {'tp_flags': []}))
    self.assertMultiLineEqual(code, textwrap.dedent("""
        int slot_seti(PyObject* self, Py_ssize_t idx, PyObject* value) {
          idx = slot::item_index(self, idx);
          if (idx < 0) return -1;
          PyObject* i = PyInt_FromSize_t(idx);
          if (i == nullptr) return -1;
          if (value != nullptr) {
            PyObject* args = PyTuple_Pack(2, i, value);
            Py_DECREF(i);
            if (args == nullptr) return -1;
            PyObject* res = wrap_get(self, args, nullptr);
            Py_DECREF(args);
            return slot::ignore(res);
          } else {
            PyErr_SetNone(PyExc_NotImplementedError);
            return -1;
          }
        }

        PySequenceMethods AsSequence = {
          nullptr,                             // sq_length
          nullptr,                             // sq_concat
          nullptr,                             // sq_repeat
          nullptr,                             // sq_item
          nullptr,                             // sq_slice
          slot_seti,                           // sq_ass_item
          nullptr,                             // sq_ass_slice
          nullptr,                             // sq_contains
          nullptr,                             // sq_inplace_concat
          nullptr,                             // sq_inplace_repeat
        };"""))

  def testSetItemMap(self):
    code = '\n'.join(
        slots.GenSlots([('__setitem__', 'wrap_get')], {'tp_flags': []}))
    self.assertMultiLineEqual(code, textwrap.dedent("""
        int slot_seto(PyObject* self, PyObject* name, PyObject* value) {
          if (value != nullptr) {
            PyObject* args = PyTuple_Pack(2, name, value);
            if (args == nullptr) return -1;
            int r = slot::ignore(wrap_get(self, args, nullptr));
            Py_DECREF(args);
            return r;
          } else {
            PyErr_SetNone(PyExc_NotImplementedError);
            return -1;
          }
        }

        PyMappingMethods AsMapping = {
          nullptr,                             // mp_length
          nullptr,                             // mp_subscript
          slot_seto,                           // mp_ass_subscript
        };"""))

  def testSizeof(self):
    with self.assertRaises(NameError):
      list(slots.GenSlots([('__sizeof__', 'wrap_so')], {'tp_flags': []}))

  def testTypeSlotsPy2(self):
    tp_slots = py2slots.PyTypeObject
    self.assertEqual(len(tp_slots), 46)
    self.assertEqual(tp_slots[0], 'tp_name')
    self.assertEqual(tp_slots[-1], 'tp_version_tag')

  def testTypeSlotsPy3(self):
    tp_slots = py3slots.PyTypeObject
    self.assertEqual(len(tp_slots), 47)
    self.assertEqual(tp_slots[0], 'tp_name')
    self.assertEqual(tp_slots[-1], 'tp_finalize')

  def testSlotFuncPy2(self):
    slots._SLOT_TYPES = {}
    for d in slots._COMMON_SLOT_MAP, slots._SLOT_MAP_PY2:
      _SlotFunc(self, d, False)

  def testSlotFuncPy3(self):
    slots._SLOT_TYPES = {}
    for d in slots._COMMON_SLOT_MAP, slots._SLOT_MAP_PY3:
      _SlotFunc(self, d, True)


def _SlotFunc(self, d, py3):
  for s in d.values():
    if s:
      if isinstance(s, str):
        s = [s]
      elif isinstance(s, int):
        continue
      else:
        s = s[0]
        if isinstance(s, str):
          s = [s]
        elif not isinstance(s, list):
          continue
      for name in s:
        self.assertTrue(slots._SlotFuncSignature(name, py3),
                        name+' func type not found')

if __name__ == '__main__':
  unittest.main()
