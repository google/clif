// Copyright 2017 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "clif/python/runtime.h"
// This should be removed once CLIF depends on Abseil.
#include <cassert>
// NOLINTNEXTLINE(whitespace/line_length) because of MOE, result is within 80.
#define CHECK_NOTNULL(condition) (assert((condition) != nullptr),(condition))

extern "C"
int Clif_PyType_Inconstructible(PyObject* self, PyObject* a, PyObject* kw) {
  PyErr_Format(PyExc_ValueError, "Class %s has no default constructor",
               Py_TYPE(self)->tp_name);
  return -1;
}

namespace clif {

void PyObjRef::Init(PyObject* self) {
  self_ = PyWeakref_NewRef(self, nullptr);
  // We don't care about non-weakrefencable objects (most likely the
  // CLIF-generated wrapper object), so nullptr is fine, just clear the error.
  PyErr_Clear();
}

void PyObjRef::HoldPyObj(PyObject* self) {
  pyowner_ = self;
  Py_INCREF(pyowner_);
}
void PyObjRef::DropPyObj() {
  Py_CLEAR(pyowner_);
}

PyObject* PyObjRef::PoisonPill() const {
  // Memory pattern mnemonic is _______CallInit.
  return reinterpret_cast<PyObject*>(0xCA771417);
}

PyObject* PyObjRef::self() const {
  if (self_ == nullptr) return nullptr;
  PyGILState_STATE threadstate = PyGILState_Ensure();
  PyObject* py = PyWeakref_GetObject(self_);
  if (py == Py_None) py = nullptr;
  Py_XINCREF(py);
  PyGILState_Release(threadstate);
  return py;
}

SafePyObject::~SafePyObject() {
  if (py_) {
    PyGILState_STATE threadstate = PyGILState_Ensure();
    Py_DECREF(py_);
    PyGILState_Release(threadstate);
  }
}

// Resource management for virtual override methods.
SafeAttr::SafeAttr(PyObject* pyobj, const char* name) {
  state_ = PyGILState_Ensure();
  meth_ = pyobj ? PyObject_GetAttrString(pyobj, name) : nullptr;
  Py_XDECREF(pyobj);  // Assume that method descriptor keeps the obj alive.
  if (meth_ == nullptr) {
    if (PyErr_ExceptionMatches(PyExc_AttributeError)) {
      PyErr_Clear();
    } else if (PyErr_Occurred()) {
      PyErr_PrintEx(0);
    }
    PyGILState_Release(state_);
  }
}
SafeAttr::~SafeAttr() {
  if (meth_ != nullptr) {
    Py_DECREF(meth_);
    PyGILState_Release(state_);
  }
}

int ClearImportCache(PyObject* module) {
  return 0;
}

// Given full.path.to.a.module.Name import module and return Name from module.
PyObject* ImportFQName(const std::string& full_class_name) {
  // Split full_class_name at the last dot.
  auto last_dot = full_class_name.find_last_of('.');
  if (last_dot == std::string::npos) {
    PyErr_Format(PyExc_ValueError, "No dot in full_class_name '%s'",
                 full_class_name.c_str());
    return nullptr;
  }
  PyObject* module = PyImport_ImportModule(
      full_class_name.substr(0, last_dot).c_str());
  if (!module) return nullptr;
  PyObject* py = PyObject_GetAttrString(
      module, full_class_name.substr(last_dot+1).c_str());
  Py_DECREF(module);
  return py;
}

// Given full.path.to.a.module.Name.A.B, and toplevel class name
// full.path.to.a.module.Name, import Name from module, and return Name.A.B.
PyObject* ImportFQName(const std::string& full_class_name,
                       const std::string& toplevel_class_name) {
  if (full_class_name == toplevel_class_name || toplevel_class_name.empty()) {
    return ImportFQName(toplevel_class_name);
  }
  if (full_class_name.rfind(toplevel_class_name + ".", 0) != 0) {
    PyErr_Format(
        PyExc_ValueError,
        "toplevel class name '%s' is not a prefix of full_class_name '%s'",
        toplevel_class_name.c_str(), full_class_name.c_str());
    return nullptr;
  }
  PyObject* py = ImportFQName(toplevel_class_name);
  auto dot = full_class_name.find_first_of('.', toplevel_class_name.size());
  while (dot != std::string::npos) {
    const auto name = dot + 1;
    const auto next_dot = full_class_name.find_first_of('.', name);
    const auto len =
        (next_dot != std::string::npos) ? next_dot - name : std::string::npos;
    const auto attr_name = full_class_name.substr(name, len);
    if (len == 0) {
      Py_DECREF(py);
      PyErr_Format(PyExc_ValueError,
                   "name '%s' is not a valid fully qualified class name",
                   full_class_name.c_str());
      return nullptr;
    }
    PyObject* next = PyObject_GetAttrString(py, attr_name.c_str());
    Py_DECREF(py);
    if (next == nullptr) {
      return nullptr;
    }
    py = next;
    dot = next_dot;
  }
  return py;
}

// py.__class__.__name__
const char* ClassName(PyObject* py) {
  /* PyPy doesn't have a separate C API for old-style classes. */
#if PY_MAJOR_VERSION < 3 && !defined(PYPY_VERSION)
  if (PyClass_Check(py))
    return PyString_AS_STRING(CHECK_NOTNULL(
        reinterpret_cast<PyClassObject*>(py)->cl_name));
  if (PyInstance_Check(py))
    return PyString_AS_STRING(CHECK_NOTNULL(
        reinterpret_cast<PyInstanceObject*>(py)->in_class->cl_name));
#endif
  if (Py_TYPE(py) == &PyType_Type) {
    return reinterpret_cast<PyTypeObject*>(py)->tp_name;
  }
  return Py_TYPE(py)->tp_name;
}

// type(py) renamed from {classobj, instance, type, class X}
const char* ClassType(PyObject* py) {
  /* PyPy doesn't have a separate C API for old-style classes. */
#if PY_MAJOR_VERSION < 3 && !defined(PYPY_VERSION)
  if (PyClass_Check(py)) return "old class";
  if (PyInstance_Check(py)) return "old class instance";
#endif
  if (Py_TYPE(py) == &PyType_Type) {
    return "class";
  }
  return "instance";
}

bool CallableNeedsNarguments(PyObject* callable, int nargs) {
  PyObject* getcallargs = ImportFQName("inspect.getcallargs");
  if (!getcallargs) return false;
  PyObject* args = PyTuple_New(nargs+1);
  Py_INCREF(callable);
  PyTuple_SET_ITEM(args, 0, callable);
  for (int i=1; i <= nargs; ++i) {
    Py_INCREF(Py_None);
    PyTuple_SET_ITEM(args, i, Py_None);
  }
  PyObject* binded = PyObject_CallObject(getcallargs, args);
  Py_DECREF(getcallargs);
  Py_DECREF(args);
  if (!binded) return false;  // PyExc_TypeError is set.
  // explicitly clear references to give to garbage collector more information
  // this potentially can cause faster collecting of unused objects
  PyDict_Clear(binded);
  Py_DECREF(binded);
  return true;
}

PyObject* DefaultArgMissedError(const char func[], char* argname) {
  PyErr_Format(PyExc_ValueError, "%s() argument %s needs a non-default value",
               func, argname);
  return nullptr;
}

PyObject* ArgError(const char func[],
                          char* argname,
                          const char ctype[],
                          PyObject* arg) {
  PyObject* exc = PyErr_Occurred();
  if (exc == nullptr) {
    PyErr_Format(
        PyExc_TypeError, "%s() argument %s is not valid for %s (%s %s given)",
        func, argname, ctype, ClassName(arg), ClassType(arg));
  } else if (exc == PyExc_TypeError) {
    PyErr_Format(
        exc, "%s() argument %s is not valid for %s (%s %s given): %s",
        func, argname, ctype, ClassName(arg), ClassType(arg),
        python::ExcStr(false).c_str());
  } else {
    PyErr_Format(
        exc, "%s() argument %s is not valid: %s",
        func, argname, python::ExcStr(false).c_str());
  }
  return nullptr;
}

namespace python {

std::string ExcStr(bool add_type) {
  PyObject* exc, *val, *tb;
  PyErr_Fetch(&exc, &val, &tb);
  if (!exc) return "";
  PyErr_NormalizeException(&exc, &val, &tb);
  std::string err;
  if (add_type) err = std::string(ClassName(exc)) + ": ";
  Py_DECREF(exc);
  if (val) {
    PyObject* val_str = PyObject_Str(val);
    Py_DECREF(val);
    if (val_str) {
#if PY_MAJOR_VERSION < 3
      err += PyString_AS_STRING(val_str);
#else
      err += PyUnicode_AsUTF8(val_str);
#endif
      Py_DECREF(val_str);
    }
  }
  Py_XDECREF(tb);
  return err;
}
}  // namespace python

// The pyclif_instance_dict_* functions are heavily modified versions of
// pybind11 code:
// http://google3/third_party/pybind11/include/pybind11/detail/class.h?l=449&rcl=276599738
extern "C" PyObject* pyclif_instance_dict_get(PyObject* self, void*) {
  PyObject** dictptr = _PyObject_GetDictPtr(self);
  if (dictptr == nullptr) {
    return nullptr;
  }
  if (*dictptr == nullptr) {
    *dictptr = PyDict_New();
  }
  Py_XINCREF(*dictptr);
  return *dictptr;
}

extern "C" int pyclif_instance_dict_set(
    PyObject* self, PyObject* new_dict, void*) {
  if (!PyDict_Check(new_dict)) {
    PyErr_Format(
        PyExc_TypeError, "__dict__ must be set to a dict, not a %s",
        Py_TYPE(new_dict)->tp_name);
    return -1;
  }
  PyObject** dictptr = _PyObject_GetDictPtr(self);
  if (dictptr == nullptr) {
    PyErr_Format(
        PyExc_SystemError,
        "pyclif_instance_dict_set dictptr == nullptr for type %s",
        Py_TYPE(self)->tp_name);
    return -1;
  }
  Py_CLEAR(*dictptr);
  *dictptr = new_dict;
  Py_INCREF(*dictptr);
  return 0;
}

extern "C" int pyclif_instance_dict_traverse(
    PyObject *self, visitproc visit, void *arg) {
  PyObject** dictptr = _PyObject_GetDictPtr(self);
  if (dictptr != nullptr) {
    Py_VISIT(*dictptr);
  }
  return 0;
}

extern "C" int pyclif_instance_dict_clear(PyObject *self) {
  PyObject** dictptr = _PyObject_GetDictPtr(self);
  if (dictptr != nullptr) {
    Py_CLEAR(*dictptr);
  }
  return 0;
}

void pyclif_instance_dict_enable(PyTypeObject* ty, std::size_t dictoffset) {
  ty->tp_dictoffset = (Py_ssize_t) dictoffset;
  // Currently the generated tp_alloc, tp_new, tp_dealloc, tp_free code is
  // incompatible with garbage collection.
  // Note: clif/testing/python/enable_instance_dict_test.py
  // includes testReferenceCycle, which doubles as a reminder.
  // Envisioned future: when switching to generating pybind11 code, this code
  // will be obsolete and purged, testReferenceCycle will "break" and then
  // adjusted to exercise the behavior with GC enabled.
  // ty->tp_flags |= Py_TPFLAGS_HAVE_GC;
  // ty->tp_traverse = pyclif_instance_dict_traverse;
  // ty->tp_clear = pyclif_instance_dict_clear;
  // tp_getset generated by gen.GetSetDef().
}

bool ensure_no_args_and_kw_args(const char* func, PyObject* args,
                                PyObject* kw) {
  if (kw != nullptr) {
    PyErr_Format(PyExc_TypeError, "%s() takes no keyword arguments", func);
    return false;
  }
  if (args != nullptr) {
    Py_ssize_t nargs = PyTuple_GET_SIZE(args);
    if (nargs != 0) {
      PyErr_Format(PyExc_TypeError, "%s() takes no arguments (%zd given)", func,
                   nargs);
      return false;
    }
  }
  return true;
}

PyObject* ReduceExImpl(PyObject* self, PyObject* args, PyObject* kw) {
  static char* kwlist[] = {C("protocol"), nullptr};
  int protocol = -1;
  if (!PyArg_ParseTupleAndKeywords(args, kw, "|i:__reduce_ex__", kwlist,
                                   &protocol)) {
    return nullptr;
  }
  // Similar to time-tested approach used in Boost.Python:
  // https://www.boost.org/doc/libs/1_55_0/libs/python/doc/v2/pickle.html
  // https://github.com/boostorg/python/blob/develop/src/object/pickle_support.cpp
  PyObject* getinitargs = PyObject_GetAttrString(self, "__getinitargs__");
  if (getinitargs == nullptr) {
    PyErr_Clear();
  }
  PyObject* getstate = PyObject_GetAttrString(self, "__getstate__");
  if (getstate == nullptr) {
    PyErr_Clear();
  }
  PyObject* setstate = PyObject_GetAttrString(self, "__setstate__");
  if (setstate == nullptr) {
    PyErr_Clear();
  }
  PyTypeObject* cls = Py_TYPE(self);
  PyObject* initargs_or_empty_tuple = nullptr;
  PyObject* empty_tuple = nullptr;
  PyObject* initargs = nullptr;
  PyObject* state = nullptr;
  PyObject* reduced = nullptr;
  const char* can_t_pickle_reason = nullptr;
  if (getinitargs == nullptr && getstate == nullptr && setstate == nullptr) {
    can_t_pickle_reason = "missing __getinitargs__ and/or __getstate__";
    goto cleanup_and_exit;
  }
  if (getstate == nullptr && setstate != nullptr) {
    can_t_pickle_reason = "has __getstate__ but missing __setstate__";
    goto cleanup_and_exit;
  }
  if (getstate != nullptr && setstate == nullptr) {
    can_t_pickle_reason = "has __setstate__ but missing __getstate__";
    goto cleanup_and_exit;
  }
  empty_tuple = PyTuple_New(0);
  if (!empty_tuple) {
    goto cleanup_and_exit;  // Keep the original error message.
  }
  if (getinitargs != nullptr) {
    initargs = PyObject_Call(getinitargs, empty_tuple, nullptr);
    if (initargs == nullptr) {
      goto cleanup_and_exit;  // Keep the original error message.
    }
    if (!PyTuple_CheckExact(initargs)) {
      // Preempts less informative exception raised otherwise in pickle module.
      if (!PyList_CheckExact(initargs)) {
        PyErr_Format(PyExc_ValueError,
                     "%s.__getinitargs__ must return a tuple or list (got %s)",
                     cls->tp_name, Py_TYPE(initargs)->tp_name);
        goto cleanup_and_exit;
      }
      // PyCLIF as-is makes it hard to return a C++ array as a Python tuple.
      // Lending a helping hand here.
      PyObject* initargs_as_tuple = PySequence_Tuple(initargs);
      if (initargs_as_tuple == nullptr) {
        goto cleanup_and_exit;  // Keep the original error message.
      }
      Py_DECREF(initargs);
      initargs = initargs_as_tuple;
    }
  }
  if (getstate != nullptr) {
    state = PyObject_Call(getstate, empty_tuple, nullptr);
    if (state == nullptr) {
      goto cleanup_and_exit;  // Keep the original error message.
    }
  }
  initargs_or_empty_tuple = (initargs != nullptr ? initargs : empty_tuple);
  if (state == nullptr) {
    reduced = Py_BuildValue("OO", (PyObject*)cls, initargs_or_empty_tuple);
  } else {
    reduced =
        Py_BuildValue("OOO", (PyObject*)cls, initargs_or_empty_tuple, state);
  }
  // Keep the original error message, if any.
cleanup_and_exit:
  if (can_t_pickle_reason != nullptr) {
    PyErr_Format(PyExc_TypeError, "can't pickle %s object: %s", cls->tp_name,
                 can_t_pickle_reason);
  }
  Py_XDECREF(getinitargs);
  Py_XDECREF(getstate);
  Py_XDECREF(setstate);
  Py_XDECREF(empty_tuple);
  Py_XDECREF(initargs);
  Py_XDECREF(state);
  return reduced;
}

}  // namespace clif
