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

"""Tests for slots."""

import textwrap
from absl.testing import absltest
from clif.python import py3slots
from clif.python import slots


class SlotsTest(absltest.TestCase):

  def testRichcmp(self):
    code = '\n'.join(
        slots.GenSlots([('__eq__', 'wrap_eq')], {'tp_flags': []}))
    self.assertMultiLineEqual(code, textwrap.dedent("""
        PyObject* slot_richcmp(PyObject* self, PyObject* other, int op) {
          switch (op) {
            case Py_EQ: return slot::adapter<wrap_eq>(self, other);
            default: Py_RETURN_NOTIMPLEMENTED;
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
    # GenSlots is still needed for its sideeffects, but the output was
    # removed in the transition to Py_TPFLAGS_HEAPTYPE.
    code = '\n'.join(
        slots.GenSlots([('__getitem__#', 'wrap_get')], {'tp_flags': []}))
    self.assertMultiLineEqual(code, textwrap.dedent(''))

  def testSetItem(self):
    code = '\n'.join(
        slots.GenSlots([('__setitem__#', 'wrap_get')], {'tp_flags': []}))
    self.assertMultiLineEqual(code, textwrap.dedent("""
        int slot_seti(PyObject* self, Py_ssize_t idx, PyObject* value) {
          idx = slot::item_index(self, idx);
          if (idx < 0) return -1;
          PyObject* i = PyLong_FromSize_t(idx);
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
        }"""))

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
        }"""))

  def testRop(self):
    code = '\n'.join(list(
        slots.GenSlots([('__add__', 'wrap_add'),
                        ('__radd__', 'wrap_radd')], {'tp_flags': []}))[:15])
    self.assertMultiLineEqual(code, textwrap.dedent("""
        extern PyTypeObject* wrapper_Type;
        PyObject* slot_nb_add(PyObject* v, PyObject* w) {
          if (PyObject_TypeCheck(v, wrapper_Type))
            return slot::adapter<wrap_add, PyObject*>(v, w);
          if (PyObject_TypeCheck(w, wrapper_Type))
            return slot::adapter<wrap_radd, PyObject*>(v, w);
          Py_INCREF(Py_NotImplemented);
          return Py_NotImplemented;
        }"""))

  def testSizeof(self):
    with self.assertRaises(NameError):
      list(slots.GenSlots([('__sizeof__', 'wrap_so')], {'tp_flags': []}))

  def testTypeSlotsPy3(self):
    tp_slots = py3slots.PyTypeObject
    self.assertLen(tp_slots, 47)
    self.assertEqual(tp_slots[0], 'tp_name')
    self.assertEqual(tp_slots[-1], 'tp_finalize')

  def testSlotFunc(self):
    slots._SLOT_TYPES = {}
    for s in slots._COMMON_SLOT_MAP.values():
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
          self.assertTrue(slots._SlotFuncSignature(name),
                          name+' func type not found')

if __name__ == '__main__':
  absltest.main()
