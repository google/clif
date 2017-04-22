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

"""Process Python __methods__ into XX_slots in CLASS_Type struct."""

# Parsed slot definitions are cached in _SLOT_MAP for the Py2 or Py3
# depending which version was called first. This is consistent with overall CLIF
# tool usage as it generates code per target version depending on invocation
# flag, ie. it's not changing in runtime.

# TODO: Decide if we need as_buffer slots implemented.

import copy
import itertools
from clif.python import py2slots
from clif.python import py3slots

I = '  '
_SLOT_MAP = {}  # Known slots cache: {py_slot_name: slot_description}


def _SplitSlots(orig_methods, py3=False):
  """Remove slot methods from orig_methods and return them."""
  if not _SLOT_MAP:
    _SLOT_MAP.update(_COMMON_SLOT_MAP)
    _SLOT_MAP.update(_SLOT_MAP_PY3 if py3 else _SLOT_MAP_PY2)
  methods = []
  slots = []
  for sc in _special_case: sc.data = {}  # {c_slot_name : s.init data}  # pylint: disable=multiple-statements
  for m in orig_methods:
    name = m[0]
    try:
      as_slot = _SLOT_MAP[name]
    except KeyError:
      methods.append(m)
    else:
      if as_slot:
        slots.extend(_SlotsFuncAddress(name.rstrip('#'), as_slot, m[1]))
      else:
        raise NameError('Redefining %s is not allowed.' % name)
  if slots:
    orig_methods[:] = methods
  return slots


def _SlotsFuncAddress(py_slot_name, slot_descr, cfunc_name):
  """Expand a [list of] slot(s) to (c_slot_name, func_addr)... generator.

  Args:
    py_slot_name: like __str__
    slot_descr: Slot description from the _SLOT_MAP
    cfunc_name: generated CFunction name like wrapFoo_as__str__
  Yields:
    ('c_slot_name', 'c_slot_func_address' | special_case_data_struct)
  """
  special = False
  if isinstance(slot_descr, tuple):
    tag = slot_descr[0]
    if isinstance(tag, int):  # A special case slot.
      special = _special_case[tag]
      c_slot_name = slot_descr[1]
      data = special.data.setdefault(c_slot_name, copy.copy(special.init))
      special(py_slot_name, cfunc_name, slot_descr, data)
      slot_descr = (c_slot_name, '')
    else:
      assert len(slot_descr) == 2, 'Wrong slot:' + str(slot_descr)
  else:
    assert isinstance(slot_descr, (list, str))
    slot_descr = (slot_descr, '')
  slots = slot_descr[0]
  if not isinstance(slots, list): slots = [slots]
  for c_slot_name in slots:
    if special:
      yield c_slot_name, special.data[c_slot_name]
    else:
      yield (c_slot_name.rstrip('#'),
             _SlotFunc(c_slot_name, cfunc_name, slot_descr[1]))


def _SlotFunc(cslot_name, cfunc_name, converter):
  """Compute c_slot_function name."""
  ret, args = _SlotFuncSignature(cslot_name)
  if isinstance(args, list) or args.strip('O'):
    assert converter, 'Non PyObject* args needs a convertor.'
    assert not converter.startswith('+'), 'Not a special processor.'
    return 'slot::'+converter+'<%s>' % cfunc_name
  args = cfunc_name + ', PyObject*'*len(args) + '>'
  if ret == 'O':
    assert not converter, ('PyObject* return from %s does not need a processor.'
                           % cfunc_name)
    return 'slot::adapter<' + args
  else:
    assert converter.startswith('+'), cslot_name+' needs a special processor.'
    return 'slot::adapter<%s, slot::%s, ' % (ret, converter[1:]) + args


def GenRichCompare(rcslots, py3=False):
  """Generate tp_richcmp slot implementation.

  Args:
    rcslots: {'Py_LT': '__lt__ wrap function name'}
    py3: Generate for Py3.
  Yields:
    C++ source
  """
  yield ''
  yield 'PyObject* slot_richcmp(PyObject* self, PyObject* other, int op) {'
  yield I+'switch (op) {'
  for op_func in rcslots.items():
    yield I+I+'case %s: return slot::adapter<%s>(self, other);' % op_func
  yield I+I+'default: return slot::noop_%s();' % ('py3' if py3 else 'py2')
  yield I+'}'
  yield '}'
GenRichCompare.name = 'slot_richcmp'  # Generated C++ name.


def GenSetAttr(setattr_slots, unused_py3=False):
  """Generate slot implementation for __set*__ / __del*__ user functions.

  Args:
    setattr_slots: [set_func, del_func]
    unused_py3: Generate for Py3.
  Yields:
    C++ source
  """
  assert len(setattr_slots) == 2, 'Need 2-slot input.'
  set_attr, del_attr = setattr_slots
  assert setattr or delattr, 'Need one or both set/del funcs.'
  yield ''
  yield 'int slot_seto(PyObject* self, PyObject* name, PyObject* value) {'
  yield I+'if (value != nullptr) {'
  if set_attr:
    yield I+I+'PyObject* args = PyTuple_Pack(2, name, value);'
    yield I+I+'if (args == nullptr) return -1;'
    yield I+I+'int r = slot::ignore(%s(self, args, nullptr));' % set_attr
    yield I+I+'Py_DECREF(args);'
    yield I+I+'return r;'
  else:
    yield I+I+'PyErr_SetNone(PyExc_NotImplementedError);'
    yield I+I+'return -1;'
  yield I+'} else {'
  if del_attr:
    yield I+I+'PyObject* args = PyTuple_Pack(1, name);'
    yield I+I+'if (args == nullptr) return -1;'
    yield I+I+'int r = slot::ignore(%s(self, args, nullptr));' % del_attr
    yield I+I+'Py_DECREF(args);'
    yield I+I+'return r;'
  else:
    yield I+I+'PyErr_SetNone(PyExc_NotImplementedError);'
    yield I+I+'return -1;'
  yield I+'}'
  yield '}'
GenSetAttr.name = 'slot_seto'  # Generated C++ name.


def GenSetItem(setitem_slots, py3=False):
  """Combine __setitem__ / __delitem__ funcs into one xx_setitem slot."""
  assert len(setitem_slots) == 2, 'Need __setitem__ / __delitem__ funcs.'
  setitem, delitem = setitem_slots
  assert setitem or delitem, 'Need one or both __setitem__ / __delitem__ funcs.'
  yield ''
  yield 'int slot_seti(PyObject* self, Py_ssize_t idx, PyObject* value) {'
  yield I+'idx = slot::item_index(self, idx);'
  yield I+'if (idx < 0) return -1;'
  yield I+'PyObject* i = Py%s_FromSize_t(idx);' % ('Long' if py3 else 'Int')
  yield I+'if (i == nullptr) return -1;'
  yield I+'if (value != nullptr) {'
  if setitem:
    yield I+I+'PyObject* args = PyTuple_Pack(2, i, value);'
    yield I+I+'Py_DECREF(i);'
    yield I+I+'if (args == nullptr) return -1;'
    yield I+I+'PyObject* res = %s(self, args, nullptr);' % setitem
    yield I+I+'Py_DECREF(args);'
    yield I+I+'return slot::ignore(res);'
  else:
    yield I+I+'PyErr_SetNone(PyExc_NotImplementedError);'
    yield I+I+'return -1;'
  yield I+'} else {'
  if delitem:
    yield I+I+'PyObject* args = PyTuple_Pack(1, i);'
    yield I+I+'Py_DECREF(i);'
    yield I+I+'if (args == nullptr) return -1;'
    yield I+I+'PyObject* res = %s(self, args, nullptr);' % delitem
    yield I+I+'Py_DECREF(args);'
    yield I+I+'return slot::ignore(res);'
  else:
    yield I+I+'PyErr_SetNone(PyExc_NotImplementedError);'
    yield I+I+'return -1;'
  yield I+'}'
  yield '}'
GenSetItem.name = 'slot_seti'  # Generated C++ name.


def _SlotLine(group, slot):
  return I+'%-36s // %s' % (group.get(slot, 'nullptr')+',', slot)


def GenAuxSlots(struct_type, struct_name, sq_group, py3=False):
  yield ''
  yield struct_type+' '+struct_name+' = {'
  for slot in getattr(py3slots if py3 else py2slots, struct_type):
    yield _SlotLine(sq_group, slot)
  yield '};'


def GenTypeSlots(tp_group, py3=False):
  for slot in (py3slots if py3 else py2slots).PyTypeObject:
    yield _SlotLine(tp_group, slot)


def GenSlots(methods, tp_slots, py3=False):
  """Generate extra slots structs and update tp_slots dict."""
  all_slots = _SplitSlots(methods)
  if all_slots:
    tp_flags = tp_slots['tp_flags']
    groups = {}
    for xx, it in itertools.groupby(sorted(all_slots), lambda s: s[0][:2]):
      xx_slots = groups[xx] = dict(it)
      if xx == 'tp':
        for s in _UpdateSlotToGeneratedFunc(xx_slots,
                                            'tp_setattro', GenSetAttr,
                                            py3): yield s
        for s in _UpdateSlotToGeneratedFunc(xx_slots,
                                            'tp_richcompare', GenRichCompare,
                                            py3): yield s
        tp_slots.update(xx_slots)
      elif xx == 'mp':
        for s in _UpdateSlotToGeneratedFunc(xx_slots,
                                            'mp_ass_subscript', GenSetAttr,
                                            py3): yield s
      elif xx == 'sq':
        for s in _UpdateSlotToGeneratedFunc(xx_slots,
                                            'sq_ass_item', GenSetItem,
                                            py3): yield s
    for xx, tp_slot, stype, sname in [
        ('nb', 'tp_as_number', 'PyNumberMethods', 'AsNumber'),
        ('sq', 'tp_as_sequence', 'PySequenceMethods', 'AsSequence'),
        ('mp', 'tp_as_mapping', 'PyMappingMethods', 'AsMapping'),
        # TODO: Implement Py3-only slots (3.5+).
        # ('am', 'tp_as_async', GenAsAsync),
    ]:
      xx_slots = groups.get(xx)
      if xx_slots:
        for s in GenAuxSlots(stype, sname, xx_slots, py3):
          yield s
        tp_slots[tp_slot] = '&' + sname
    # Update tp_flags.
    if py3:
      if 'tp_finalize' in tp_slots:
        tp_flags.append('Py_TPFLAGS_HAVE_FINALIZE')
    # else: We skip flags that are already in Py_TPFLAGS_DEFAULT.


def _UpdateSlotToGeneratedFunc(slots, name, gen_func, py3):
  data = slots.get(name)
  if data:
    for s in gen_func(data, py3): yield s  # pylint: disable=multiple-statements
    slots[name] = gen_func.name


def _ATTRcase(slot, func, unused_slot_info, case_data):
  # pylint: disable=multiple-statements
  if slot.startswith('__set'): case_data[0] = func
  elif slot.startswith('__del'): case_data[1] = func
  else: assert 'Slot %s should not be _ATTR special.' % slot
_ATTRcase.init = [None, None]


def _ITEMcase(slot, func, unused_slot_info, case_data):
  # pylint: disable=multiple-statements
  if slot == '__setitem__': case_data[0] = func
  elif slot == '__delitem__': case_data[1] = func
  else: assert 'Slot %s should not be _ITEM special.' % slot
_ITEMcase.init = [None, None]


def _RICHcase(unused_slot, func, slot_info, case_data):
  assert len(slot_info) == 3
  case_data[slot_info[-1]] = func
_RICHcase.init = {}


FORBIDDEN = ()  # Redefining those slots gets an error.
# Special cases.
_ATTR, _ITEM, _RICH = range(3)
_special_case = [_ATTRcase, _ITEMcase, _RICHcase]
# Some known "slots" are not in the map, they are ignored and if defined just
# will be methods (to be called from a Python class inherited from ours).
_COMMON_SLOT_MAP = {
    # name : 'slot' or ['slots',...]  call adapter<>
    # name : (slot(s), 'processor')   call processor
    # name : (slot(s), '+converter')  call adapter<> with result converter
    # name : (CASE, slot)             use _special_case[CASE] func
    # name : (CASE, slots, op)        use _special_case[CASE] func
    # name : FORBIDDEN
    '__new__': FORBIDDEN,
    '__del__': FORBIDDEN,
    '__getattr__': 'tp_getattro',
    '__setattr__': (_ATTR, 'tp_setattro'),
    '__delattr__': (_ATTR, 'tp_setattro'),
    '__getattribute__': FORBIDDEN,
    '__dir__': FORBIDDEN,
    '__get__': FORBIDDEN,
    '__set__': FORBIDDEN,
    '__delete__': FORBIDDEN,
    '__len__': (['sq_length', 'mp_length'], '+as_size'),
    '__hash__': ('tp_hash', '+as_hash'),
    '__getitem__': 'mp_subscript',
    '__setitem__': (_ATTR, 'mp_ass_subscript'),
    '__delitem__': (_ATTR, 'mp_ass_subscript'),
    '__getitem__#': ('sq_item', 'getitem'),
    '__setitem__#': (_ITEM, 'sq_ass_item'),
    '__delitem__#': (_ITEM, 'sq_ass_item'),
    '__concat__': 'sq_concat',
    '__contains__': ('sq_contains', '+as_bool'),
    '__str__': 'tp_str',
    '__repr__': 'tp_repr',
    '__format__': FORBIDDEN,
    '__sizeof__': FORBIDDEN,
    '__pos__': 'nb_positive',
    '__neg__': 'nb_negative',
    '__abs__': 'nb_absolute',
    '__add__': ['nb_add', 'sq_concat'],
    '__iadd__': ['nb_inplace_add', 'sq_inplace_concat'],
    '__sub__': 'nb_subtract',
    '__isub__': 'nb_inplace_subtract',
    '__mul__': 'nb_multiply',
    '__imul__': 'nb_inplace_multiply',
    '__truediv__': 'nb_true_divide',
    '__itruediv__': 'nb_inplace_true_divide',
    '__floordiv__': 'nb_floor_divide',
    '__ifloordiv__': 'nb_inplace_floor_divide',
    '__divmod__': 'nb_divmod',
    '__mod__': 'nb_remainder',
    '__imod__': 'nb_inplace_remainder',
    '__pow__': 'nb_power',
    '__ipow__': 'nb_inplace_power',
    '__lshift__': 'nb_lshift',
    '__ilshift__': 'nb_inplace_lshift',
    '__rshift__': 'nb_rshift',
    '__irshift__': 'nb_inplace_rshift',
    '__and__': 'nb_and',
    '__iand__': 'nb_inplace_and',
    '__xor__': 'nb_xor',
    '__ixor__': 'nb_inplace_xor',
    '__or__': 'nb_or',
    '__ior__': 'nb_inplace_or',
    '__invert__': 'nb_invert',
    '__int__': 'nb_int',
    '__float__': 'nb_float',
    '__index__': 'nb_index',
    '__iter__': 'tp_iter',
    '__next__': 'tp_iternext',
    '__lt__': (_RICH, 'tp_richcompare', 'Py_LT'),
    '__le__': (_RICH, 'tp_richcompare', 'Py_LE'),
    '__gt__': (_RICH, 'tp_richcompare', 'Py_GT'),
    '__ge__': (_RICH, 'tp_richcompare', 'Py_GE'),
    '__eq__': (_RICH, 'tp_richcompare', 'Py_EQ'),
    '__ne__': (_RICH, 'tp_richcompare', 'Py_NE'),
}
_SLOT_MAP_PY2 = {
    '__coerce__': FORBIDDEN,
    '__div__': 'nb_divide',
    '__idiv__': 'nb_inplace_divide',
    '__long__': 'nb_long',
    '__cmp__': ('tp_compare', '+as_cmp'),
    '__nonzero__': ('nb_nonzero', '+as_bool'),
}
_SLOT_MAP_PY3 = {
    '__bool__': ('nb_bool', '+as_bool'),
    # Enable for Python 3.5+
    # '__matmul__': 'nb_matrix_multiply',
    # '__imatmul__': 'nb_inplace_matrix_multiply',
    # '__await__': 'am_await',
    # '__aiter__': 'am_aiter',
    # '__anext__': 'am_anext',
}


def _SlotFuncSignature(slot, py3=False):
  return (py3slots if py3 else py2slots).SIGNATURES[slot]
