// Copyright 2023 Google LLC
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

#include <Python.h>

#include "absl/log/check.h"

namespace clif {

namespace {

#if PY_VERSION_HEX < 0x030B0000

bool ClsGetStateIsBaseObjectGetstate(PyTypeObject*) { return false; }

#else

// The object.__getstate__() added with
// https://github.com/python/cpython/pull/2821
// is not suitable for extension types.
bool ClsGetStateIsBaseObjectGetstate(PyTypeObject* cls) {
  PyObject* base_getstate =
      PyObject_GetAttrString((PyObject*)&PyBaseObject_Type, "__getstate__");
  CHECK(base_getstate != nullptr);
  PyObject* cls_getstate =
      PyObject_GetAttrString((PyObject*)cls, "__getstate__");
  if (cls_getstate == nullptr) {
    PyErr_Clear();
    Py_DECREF(base_getstate);
    return false;
  }
  bool retval = (cls_getstate == base_getstate);
  Py_DECREF(cls_getstate);
  Py_DECREF(base_getstate);
  return retval;
}

#endif

}  // namespace

PyObject* ReduceExCore(PyObject* self, const int protocol) {
  PyTypeObject* cls = Py_TYPE(self);
  // Similar to time-tested approach used in Boost.Python:
  // https://www.boost.org/doc/libs/1_55_0/libs/python/doc/v2/pickle.html
  // https://github.com/boostorg/python/blob/develop/src/object/pickle_support.cpp
  PyObject* getinitargs = PyObject_GetAttrString(self, "__getinitargs__");
  if (getinitargs == nullptr) {
    PyErr_Clear();
  }
  PyObject* getstate = nullptr;
  if (!ClsGetStateIsBaseObjectGetstate(cls)) {
    getstate = PyObject_GetAttrString(self, "__getstate__");
    if (getstate == nullptr) {
      PyErr_Clear();
    }
  }
  PyObject* setstate = PyObject_GetAttrString(self, "__setstate__");
  if (setstate == nullptr) {
    PyErr_Clear();
  }
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
