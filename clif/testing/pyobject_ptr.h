/*
 * Copyright 2023 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#ifndef CLIF_TESTING_PYOBJECT_PTR_H_
#define CLIF_TESTING_PYOBJECT_PTR_H_

#include <Python.h>

#include <functional>

namespace clif_testing_pyobject_ptr {

// For use as a temporary user-defined object, to maximize sensitivity of the
// unit tests.
struct CppValueHolder {
  // Default ctor required for PyCLIF-C-API, unfortunately (but not for
  // PyCLIF-pybind11):
  CppValueHolder() : value{-987} {}
  CppValueHolder(int value) : value{value} {}
  int value;
};

inline PyObject *return_pyobject_ptr() { return PyLong_FromLongLong(2314L); }

inline bool pass_pyobject_ptr(PyObject *obj) {
  return static_cast<bool>(PyTuple_CheckExact(obj));
}

inline PyObject *call_callback_with_pyobject_ptr_return(
    const std::function<PyObject *(const CppValueHolder &mode)> &cb,
    const CppValueHolder &mode) {
  return cb(mode);
}

inline CppValueHolder call_callback_with_pyobject_ptr_arg(
    const std::function<CppValueHolder(PyObject *)> &cb, PyObject *obj) {
  return cb(obj);
}

inline CppValueHolder call_callback_with_pyobject_ptr_int_args(
    const std::function<CppValueHolder(PyObject *, int)> &cb, PyObject *obj) {
  return cb(obj, 40);
}

inline CppValueHolder call_callback_with_int_pyobject_ptr_args(
    const std::function<CppValueHolder(int, PyObject *)> &cb, PyObject *obj) {
  return cb(50, obj);
}

}  // namespace clif_testing_pyobject_ptr

#endif  // CLIF_TESTING_PYOBJECT_PTR_H_
