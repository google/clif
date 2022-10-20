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

#include "third_party/pybind11/include/pybind11/pybind11.h"

// NOLINTNEXTLINE
#include <type_traits>

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

inline Py_ssize_t item_index(Py_ssize_t idx, Py_ssize_t length) {
  if (idx < -length || idx >= length) {
    return -1;
  }
  return idx < 0 ? idx + length : idx;
}

// The implementation of these `HasClifPyObjAs` functions are identical with the
// `HasClifConversion` defined in clif/python/stltypes.h. I have to
// copy them here because at the time these functions are defined, the
// `Clif_PyObj` functions should be visible.
template <typename T,
          typename R = decltype(
              Clif_PyObjAs(std::declval<PyObject*>(), std::declval<T*>()))>
constexpr bool HasNonClifPyObjAs(int) {
  static_assert(std::is_same<R, bool>::value, "");
  return true;
}

template <typename T>
constexpr bool HasNonClifPyObjAs(...) {
  return false;
}

template <typename T,
          typename R = decltype(
              ::clif::Clif_PyObjAs(std::declval<PyObject*>(),
                                   std::declval<T*>()))>
constexpr bool HasClifPyObjAs(int) {
  static_assert(std::is_same<R, bool>::value, "");
  return true;
}

template <typename T>
constexpr bool HasClifPyObjAs(...) {
  return HasNonClifPyObjAs<T>(0);
}

template <typename T,
          typename R = decltype(
              Clif_PyObjFrom(std::declval<T>(),
                             std::declval<::clif::py::PostConv>()))>
constexpr bool HasNonClifPyObjFrom(int) {
  static_assert(std::is_same<R, PyObject*>::value, "");
  return true;
}

template <typename T>
constexpr bool HasNonClifPyObjFrom(...) {
  return false;
}

template <typename T,
          typename R = decltype(
              ::clif::Clif_PyObjFrom(std::declval<T>(),
                                     std::declval<::clif::py::PostConv>()))>
constexpr bool HasClifPyObjFrom(int) {
  static_assert(std::is_same<R, PyObject*>::value, "");
  return true;
}

template <typename T>
constexpr bool HasClifPyObjFrom(...) {
  return HasNonClifPyObjFrom<T>(0);
}

template <typename T>
constexpr bool HasPyObjAs() {
  return HasClifPyObjAs<T>(0);
}

// `absl::optional` does not work with abstract types. Calling
// `HasPyObjAs<absl::optional<Abstract>>` results in compilation errors.
// Use this as a workaround.
template <typename T,
          std::enable_if_t<!std::is_abstract_v<T>, int> = 0>
constexpr bool HasAbslOptionalPyObjAsFalseIfAbstract() {
  return HasClifPyObjAs<absl::optional<T>>(0);
}

template <typename T,
          std::enable_if_t<std::is_abstract_v<T>, int> = 0>
constexpr bool HasAbslOptionalPyObjAsFalseIfAbstract() {
  return false;
}

template <typename T>
constexpr bool HasPyObjFrom() {
  return HasClifPyObjFrom<T>(0);
}

}  // namespace clif

namespace pybind11 {
namespace detail {

#define CLIF_TYPE_CASTER_CAST                                                  \
  template<class T = Type,                                                     \
           std::enable_if_t<clif::HasPyObjFrom<T>(), int> = 0>                 \
  static handle cast(Type& src, return_value_policy /* policy */,              \
                     handle /* parent */) {                                    \
    using ::clif::Clif_PyObjFrom;                                              \
    return Clif_PyObjFrom(std::move(src), {});                                 \
  }                                                                            \
                                                                               \
  template<class T = Type,                                                     \
           std::enable_if_t<clif::HasPyObjFrom<T>(), int> = 0>                 \
  static handle cast(const Type& src, return_value_policy /* policy */,        \
                     handle /* parent */) {                                    \
    using ::clif::Clif_PyObjFrom;                                              \
    return Clif_PyObjFrom(std::move(src), {});                                 \
  }                                                                            \
                                                                               \
  template<class T = Type,                                                     \
           std::enable_if_t<clif::HasPyObjFrom<T>(), int> = 0>                 \
  static handle cast(Type&& src, return_value_policy /* policy */,             \
                     handle /* parent */) {                                    \
    using ::clif::Clif_PyObjFrom;                                              \
    return Clif_PyObjFrom(std::move(src), {});                                 \
  }                                                                            \
                                                                               \
  template<typename T = Type,                                                  \
           std::enable_if_t<clif::HasPyObjFrom<T*>(), int> = 0>                \
  static handle cast(Type* src, return_value_policy /* policy */,              \
                     handle /* parent */) {                                    \
    using ::clif::Clif_PyObjFrom;                                              \
    return Clif_PyObjFrom(src, {});                                            \
  }                                                                            \
                                                                               \
  template<typename T = Type,                                                  \
           std::enable_if_t<clif::HasPyObjFrom<T*>(), int> = 0>                \
  static handle cast(const Type* src, return_value_policy /* policy */,        \
                     handle /* parent */) {                                    \
    using ::clif::Clif_PyObjFrom;                                              \
    return Clif_PyObjFrom(src, {});                                            \
  }                                                                            \
                                                                               \
  template<typename T = Type,                                                  \
           std::enable_if_t<clif::HasPyObjFrom<T**>(), int> = 0>               \
  static handle cast(Type** src, return_value_policy /* policy */,             \
                     handle /* parent */) {                                    \
    using ::clif::Clif_PyObjFrom;                                              \
    return Clif_PyObjFrom(src, {});                                            \
  }                                                                            \

template <typename Type, bool is_type_abstract = std::is_abstract_v<Type>,
          bool has_customized_optional_conversion = !clif::HasPyObjAs<Type>() &&
              clif::HasAbslOptionalPyObjAsFalseIfAbstract<Type>()>
struct clif_type_caster {
 public:
  PYBIND11_TYPE_CASTER(Type, const_name<Type>());

  CLIF_TYPE_CASTER_CAST

  // TODO: Add load function when
  // `Clif_PyObjAs(PyObject*, Type**) or
  template<class T = Type,
           std::enable_if_t<clif::HasPyObjAs<T>(), int> = 0>
  bool load(handle src, bool) {
    using ::clif::Clif_PyObjAs;
    return Clif_PyObjAs(src.ptr(), &value);
  }
};

template <typename Type>
struct clif_type_caster<Type, false, true> {
 public:
  static constexpr auto name = const_name<Type>();

  CLIF_TYPE_CASTER_CAST

  bool load(handle src, bool) {
    using ::clif::Clif_PyObjAs;
    return Clif_PyObjAs(src.ptr(), &value);
  }

  template <typename T_>
  using cast_op_type = movable_cast_op_type<T_>;

  operator Type *() { return &(value.value()); }
  operator Type &() { return value.value(); }
  operator Type &&() && { return std::move(value.value()); }

 private:
  absl::optional<Type> value;
};

template <typename Type>
struct clif_type_caster<Type, true, false> {
 public:
  static constexpr auto name = const_name<Type>();

  CLIF_TYPE_CASTER_CAST

  // For abstract types, legacy PyCLIF expects either
  // `Clif_PyObjAs(PyObject*, std::unique_ptr<AbstractType>*)` or
  // `Clif_PyObjAs(PyObject*, AbstractType**)` to exist.
  // TODO: Add load function when only
  // `Clif_PyObjAs(PyObject*, AbstractType**) exist.
  template<class T = Type,
           std::enable_if_t<
              clif::HasPyObjAs<std::unique_ptr<T>>(), int> = 0>
  bool load(handle src, bool) {
    // TODO: Test with two passes in pybind11 dispatcher.
    std::unique_ptr<Type> res;
    using ::clif::Clif_PyObjAs;
    if (!Clif_PyObjAs(src.ptr(), &res)) {
      return false;
    }
    value = std::move(res);
    return true;
  }

  template <typename T_>
  using cast_op_type = movable_cast_op_type<T_>;

  operator Type *() { return value.get(); }
  operator Type &() { return *value; }
  operator Type &&() && { return std::move(*value); }

 private:
  std::unique_ptr<Type> value;
};

template <typename Type, typename HolderType>
struct clif_smart_ptr_type_caster {
 public:
  PYBIND11_TYPE_CASTER(HolderType, const_name<Type>());

  template<typename T = HolderType,
           std::enable_if_t<clif::HasPyObjAs<T>(), int> = 0>
  bool load(handle src, bool) {
    using ::clif::Clif_PyObjAs;
    return Clif_PyObjAs(src.ptr(), &value);
  }

  template<typename T = HolderType,
           std::enable_if_t<clif::HasPyObjFrom<T>(), int> = 0>
  static handle cast(T src, return_value_policy /* policy */,
                     handle /* parent */) {
    using ::clif::Clif_PyObjFrom;
    return Clif_PyObjFrom(std::move(src), {});
  }
};

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
