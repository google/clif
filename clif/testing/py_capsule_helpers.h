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

#ifndef CLIF_TESTING_PY_CAPSULE_HELPERS_H_
#define CLIF_TESTING_PY_CAPSULE_HELPERS_H_

#include <Python.h>

#include <cassert>
#include <memory>

#include "absl/log/log.h"

namespace clif_testing::py_capsule_helpers {

template <typename PayloadType>
PyObject* MakePyCapsuleWithPayloadPointer(
    std::unique_ptr<PayloadType>&& payload) {
  return PyCapsule_New(
      payload.release(), typeid(PayloadType*).name(), [](PyObject* self) {
        void* void_ptr =
            PyCapsule_GetPointer(self, typeid(PayloadType*).name());
        if (PyErr_Occurred()) {
          PyErr_Print();
          LOG(FATAL) << "UNEXPECTED Python exception (sent to stderr).";
        }
        assert(void_ptr != nullptr);
        delete static_cast<PayloadType*>(void_ptr);
      });
}

template <typename PayloadType>
bool GetPayloadPointerFromPyCapsule(PyObject* py_obj, PayloadType** c_obj) {
  void* void_ptr = PyCapsule_GetPointer(py_obj, typeid(PayloadType*).name());
  if (void_ptr == nullptr) {
    return false;
  }
  *c_obj = static_cast<PayloadType*>(void_ptr);
  return true;
}

template <typename PayloadType>
bool GetPayloadFromPyCapsule(PyObject* py_obj, PayloadType* c_obj) {
  void* void_ptr = PyCapsule_GetPointer(py_obj, typeid(PayloadType*).name());
  if (void_ptr == nullptr) {
    return false;
  }
  *c_obj = *(static_cast<PayloadType*>(void_ptr));
  return true;
}

}  // namespace clif_testing::py_capsule_helpers

#endif  // CLIF_TESTING_PY_CAPSULE_HELPERS_H_
