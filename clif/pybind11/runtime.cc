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

#include "third_party/pybind11/include/pybind11/pybind11.h"

// NOLINTNEXTLINE
#include "absl/log/check.h"
#include "clif/pybind11/runtime.h"
#include "clif/python/pickle_support.h"
#include "clif/python/runtime.h"

namespace clif {

Py_ssize_t item_index(Py_ssize_t idx, Py_ssize_t length) {
  if (idx < -length || idx >= length) {
    return -1;
  }
  return idx < 0 ? idx + length : idx;
}

void ThrowErrorAlreadySetIfPythonErrorOccurred() {
  if (PyErr_Occurred()) {
    throw pybind11::error_already_set();
  }
}

bool ThrowErrorAlreadySetIfFalse(bool success) {
  ThrowErrorAlreadySetIfPythonErrorOccurred();
  if (!success) {
    throw pybind11::error_already_set();
  }
  return true;
}

bool ClearClif_PyObjAsPythonErrorIfFalse(bool success) {
  if (success) {
    clif::LogFatalIfPythonErrorOccurred();
    return true;
  }
  CHECK(PyErr_Occurred());
  PyErr_Clear();
  return false;
}

}  // namespace clif

namespace clif_pybind11 {

pybind11::object ReduceExImpl(pybind11::handle self, int protocol) {
  PyObject* reduced = ::clif::ReduceExCore(self.ptr(), protocol);
  if (reduced == nullptr) {
    throw pybind11::error_already_set();
  }
  return pybind11::reinterpret_steal<pybind11::object>(reduced);
}

}  // namespace clif_pybind11
