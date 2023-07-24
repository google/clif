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
#ifndef CLIF_TESTING_PROPERTY_GET_SET_CPP_DERIVED_H_
#define CLIF_TESTING_PROPERTY_GET_SET_CPP_DERIVED_H_

#include <Python.h>

namespace clif_testing_property_get_set_cpp_derived {

struct Inty {
  int value = -999;
  Inty() = default;
  explicit Inty(int n) : value(n) {}
};

struct IntyArg : Inty {
  IntyArg() : Inty() {}
  explicit IntyArg(int n) : Inty(n) {}
};

// CLIF use `::clif_testing_property_get_set_cpp_derived::IntyArg` as IntyArg

inline bool Clif_PyObjAs(PyObject* py, IntyArg* c) {
  if (!PyLong_Check(py)) {
    PyErr_SetString(PyExc_TypeError, "cannot convert to Inty");
    return false;
  }
  long val = PyLong_AsLong(py);  // NOLINT(runtime/int)
  if (PyErr_Occurred()) {
    return false;
  }
  *c = IntyArg(static_cast<int>(val % 1000));
  return true;
}

struct IntyHolder {
  Inty memb;
  const Inty& get_memb() const { return memb; }
  void set_memb(const Inty& new_value) { memb = new_value; }
};

}  // namespace clif_testing_property_get_set_cpp_derived

#endif  // CLIF_TESTING_PROPERTY_GET_SET_CPP_DERIVED_H_
