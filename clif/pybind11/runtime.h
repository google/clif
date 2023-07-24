// Copyright 2021 Google LLC
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

#ifndef THIRD_PARTY_CLIF_PYBIND11_RUNTIME_H_
#define THIRD_PARTY_CLIF_PYBIND11_RUNTIME_H_

#include "third_party/pybind11/include/pybind11/smart_holder.h"
#include "third_party/pybind11/include/pybind11/type_caster_pyobject_ptr.h"

#include "clif/python/stltypes.h"
#include "third_party/pybind11_abseil/absl_casters.h"
#include "util/task/python/clif/status_return_override.h"

namespace clif {

template <typename T>
struct CapsuleWrapper {
  explicit CapsuleWrapper(): ptr(nullptr) { }
  explicit CapsuleWrapper(T p): ptr(p) { }
  T ptr;
};

Py_ssize_t item_index(Py_ssize_t idx, Py_ssize_t length);

void ThrowErrorAlreadySetIfPythonErrorOccurred();
bool ThrowErrorAlreadySetIfFalse(bool success);

}  // namespace clif

namespace pybind11 {
namespace detail {

template <typename T>
struct type_caster<clif::CapsuleWrapper<T>> {
 public:
  PYBIND11_TYPE_CASTER(clif::CapsuleWrapper<T>, _<clif::CapsuleWrapper<T>>());

  bool load(handle src, bool convert) {
    if (isinstance<capsule>(src)) {
      value = clif::CapsuleWrapper<T>(reinterpret_borrow<capsule>(src.ptr()));
      return true;
    }
    void* void_ptr_from_void_ptr_capsule
        = try_as_void_ptr_capsule_get_pointer(src, typeid(T).name());
    if (void_ptr_from_void_ptr_capsule) {
      value = clif::CapsuleWrapper<T>(
        static_cast<T>(void_ptr_from_void_ptr_capsule));
      return true;
    }
    return false;
  }

  static handle cast(
      clif::CapsuleWrapper<T> src, return_value_policy, handle) {
    return capsule(src.ptr, typeid(T).name()).release();
  }
};

}  // namespace detail
}  // namespace pybind11

#endif  // THIRD_PARTY_CLIF_PYBIND11_RUNTIME_H_
