/*
 * Copyright 2023 Google Inc.
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
#ifndef THIRD_PARTY_CLIF_PYTHON_PYOBJECT_PTR_CONV_H_
#define THIRD_PARTY_CLIF_PYTHON_PYOBJECT_PTR_CONV_H_

#include <Python.h>

#include "glog/logging.h"

#include "clif/python/postconv.h"

namespace clif {

inline PyObject* Clif_PyObjFrom(PyObject* c, const py::PostConv&) {
  // Ignore post conversion for object output.
  if (c == nullptr && !PyErr_Occurred()) {
    PyErr_SetString(PyExc_SystemError,
                    "When returning the NULL object, exception must be set");
  }
  return c;
}

inline bool Clif_PyObjAs(PyObject* py, PyObject** c) {
  CHECK(c != nullptr);
  CHECK(py != nullptr);
  *c = py;  // Borrow reference from Python for C++ processing.
  return true;
}

}  // namespace clif

#endif  // THIRD_PARTY_CLIF_PYTHON_PYOBJECT_PTR_CONV_H_
