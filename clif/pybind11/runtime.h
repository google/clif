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

#include "Python.h"

#include "third_party/pybind11/include/pybind11/pybind11.h"
#include "third_party/pybind11_abseil/absl_casters.h"
#include "util/task/python/clif/patch_status_bindings.h"
#include "util/task/python/clif/status_return_overload.h"

namespace clif {

template <typename T>
struct CapsuleWrapper {
  explicit CapsuleWrapper(): ptr(nullptr) { }
  explicit CapsuleWrapper(T p): ptr(p) { }
  T ptr;
};

inline Py_ssize_t item_index(Py_ssize_t idx, Py_ssize_t length) {
  if (idx < -length || idx >= length) {
    return -1;
  }
  return idx < 0 ? idx + length : idx;
}

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
    return false;
  }

  static handle cast(
      clif::CapsuleWrapper<T> src, return_value_policy, handle) {
    return capsule(src.ptr, typeid(T).name()).release();
  }
};

template <>
class type_caster<PyObject> {
 public:
  static constexpr auto name = const_name("PyObject *");

  // Conversion part 1 (C++ -> Python)
  static handle cast(PyObject* src, return_value_policy, handle) {
    return reinterpret_borrow<object>(src).release();
  }

  // Conversion part 2 (Python->C++)
  bool load(handle src, bool convert) {
    value = reinterpret_borrow<object>(src);
    return true;
  }

  template <typename T>
  using cast_op_type = PyObject *;

  explicit operator PyObject *() {
    return value.ptr();
  }

 private:
  object value;
};

}  // namespace detail
}  // namespace pybind11


// These two macros are nearly the same with the macros defined in
// third_party/pybind11, but with the module init function name changed from
// `PyInit_<modulename>` to `GooglePyInit_<modulename>`. This is to allow the
// static importer (/devtools/python/launcher/static_metaimporter.cc) to find
// and statically link the generated extension module. See
// https://g3doc.corp.google.com/devtools/python/g3doc/python-extensions.md
// for more information.
#define GOOGLE_PYBIND11_PLUGIN_IMPL(symbol)                                   \
    extern "C" PYBIND11_MAYBE_UNUSED PYBIND11_EXPORT PyObject                 \
        *GooglePyInit_##symbol(void);                                         \
    extern "C" PYBIND11_EXPORT PyObject *GooglePyInit_##symbol(void)

#define GOOGLE_PYBIND11_MODULE(name, symbol, variable)                        \
    static ::pybind11::module_::module_def PYBIND11_CONCAT(                   \
        pybind11_module_def_, name) PYBIND11_MAYBE_UNUSED;                    \
    PYBIND11_MAYBE_UNUSED                                                     \
    static void PYBIND11_CONCAT(pybind11_init_, name)(::pybind11::module_ &); \
    GOOGLE_PYBIND11_PLUGIN_IMPL(symbol) {                                     \
        PYBIND11_CHECK_PYTHON_VERSION                                         \
        PYBIND11_ENSURE_INTERNALS_READY                                       \
        auto m = ::pybind11::module_::create_extension_module(                \
            PYBIND11_TOSTRING(name), nullptr, &PYBIND11_CONCAT(               \
                pybind11_module_def_, name));                                 \
        try {                                                                 \
            PYBIND11_CONCAT(pybind11_init_, name)(m);                         \
            return m.ptr();                                                   \
        }                                                                     \
        PYBIND11_CATCH_INIT_EXCEPTIONS                                        \
    }                                                                         \
    void PYBIND11_CONCAT(pybind11_init_, name)(::pybind11::module_ & (variable))


#endif  // THIRD_PARTY_CLIF_PYBIND11_RUNTIME_H_
