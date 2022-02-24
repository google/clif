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
#include "util/task/python/clif/patch_status_bindings.h"

namespace clif {

inline pybind11::object ConvertPyObject(PyObject* ptr) {
  if (PyErr_Occurred() || ptr == nullptr) {
    throw pybind11::error_already_set();
  }
  return pybind11::reinterpret_borrow<pybind11::object>(ptr);
}

template <typename T>
struct CapsuleWrapper {
  explicit CapsuleWrapper(): ptr(nullptr) { }
  explicit CapsuleWrapper(T p): ptr(p) { }
  T ptr;
};

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
