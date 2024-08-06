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

#ifndef CLIF_PYBIND11_CLIF_TYPE_CASTERS_H_
#define CLIF_PYBIND11_CLIF_TYPE_CASTERS_H_

// pybind11 includes have to be at the very top, even before Python.h
#include "third_party/pybind11/include/pybind11/pybind11.h"

// Must be after pybind11 include.
#include <Python.h>

// NOLINTNEXTLINE
#include <type_traits>

#include "clif/pybind11/runtime.h"
#include "clif/pybind11/status_return_override.h"
#include "clif/python/postconv.h"
#include "clif/python/pyobject_ptr_conv.h"
#include "clif/python/types.h"

namespace clif_pybind11 {

// The implementation of these `HasClifPyObjAs` functions are identical with the
// `HasClifConversion` defined in clif/python/stltypes.h. I have to
// copy them here because at the time these functions are defined, the
// `Clif_PyObj` functions should be visible.
template <typename T, typename R = decltype(Clif_PyObjAs(
                          std::declval<PyObject*>(), std::declval<T*>()))>
constexpr bool HasNonClifPyObjAs(int) {
  static_assert(std::is_same<R, bool>::value, "");
  return true;
}

template <typename T>
constexpr bool HasNonClifPyObjAs(...) {
  return false;
}

template <typename T, typename R = decltype(::clif::Clif_PyObjAs(
                          std::declval<PyObject*>(), std::declval<T*>()))>
constexpr bool HasClifPyObjAs(int) {
  static_assert(std::is_same<R, bool>::value, "");
  return true;
}

template <typename T>
constexpr bool HasClifPyObjAs(...) {
  return HasNonClifPyObjAs<T>(0);
}

template <typename T,
          typename R = decltype(Clif_PyObjFrom(
              std::declval<T>(), std::declval<::clif::py::PostConv>()))>
constexpr bool HasNonClifPyObjFrom(int) {
  static_assert(std::is_same<R, PyObject*>::value, "");
  return true;
}

template <typename T>
constexpr bool HasNonClifPyObjFrom(...) {
  return false;
}

template <typename T,
          typename R = decltype(::clif::Clif_PyObjFrom(
              std::declval<T>(), std::declval<::clif::py::PostConv>()))>
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

// `std::optional` does not work with abstract types. Calling
// `HasPyObjAs<std::optional<Abstract>>` results in compilation errors.
// Use this as a workaround.
template <typename T, std::enable_if_t<!std::is_abstract_v<T>, int> = 0>
constexpr bool HasAbslOptionalPyObjAsFalseIfAbstract() {
  return HasNonClifPyObjAs<std::optional<T>>(0);
}

template <typename T, std::enable_if_t<std::is_abstract_v<T>, int> = 0>
constexpr bool HasAbslOptionalPyObjAsFalseIfAbstract() {
  return false;
}

template <typename T>
constexpr bool HasPyObjFrom() {
  return HasClifPyObjFrom<T>(0);
}

pybind11::object ReduceExImpl(pybind11::handle self, int protocol);

clif::py::PostConv PostConvFromReturnValuePolicyPack(const rvp_or_rvpp& rvpp);

}  // namespace clif_pybind11

namespace pybind11 {
namespace detail {

#define CLIF_TYPE_CASTER_CAST                                              \
  template <class T = Type,                                                \
            std::enable_if_t<clif_pybind11::HasPyObjFrom<T>(), int> = 0>   \
  static handle cast(Type& src, const ::clif_pybind11::rvp_or_rvpp& rvpp,  \
                     handle /* parent */) {                                \
    using ::clif::Clif_PyObjFrom;                                          \
    return Clif_PyObjFrom(                                                 \
        std::move(src),                                                    \
        clif_pybind11::PostConvFromReturnValuePolicyPack(rvpp));           \
  }                                                                        \
                                                                           \
  template <class T = Type,                                                \
            std::enable_if_t<clif_pybind11::HasPyObjFrom<T>(), int> = 0>   \
  static handle cast(const Type& src,                                      \
                     const ::clif_pybind11::rvp_or_rvpp& rvpp,             \
                     handle /* parent */) {                                \
    using ::clif::Clif_PyObjFrom;                                          \
    return Clif_PyObjFrom(                                                 \
        std::move(src),                                                    \
        clif_pybind11::PostConvFromReturnValuePolicyPack(rvpp));           \
  }                                                                        \
                                                                           \
  template <class T = Type,                                                \
            std::enable_if_t<clif_pybind11::HasPyObjFrom<T>(), int> = 0>   \
  static handle cast(Type&& src, const ::clif_pybind11::rvp_or_rvpp& rvpp, \
                     handle /* parent */) {                                \
    using ::clif::Clif_PyObjFrom;                                          \
    return Clif_PyObjFrom(                                                 \
        std::move(src),                                                    \
        clif_pybind11::PostConvFromReturnValuePolicyPack(rvpp));           \
  }                                                                        \
                                                                           \
  template <typename T = Type,                                             \
            std::enable_if_t<clif_pybind11::HasPyObjFrom<T*>(), int> = 0>  \
  static handle cast(Type* src, const ::clif_pybind11::rvp_or_rvpp& rvpp,  \
                     handle /* parent */) {                                \
    using ::clif::Clif_PyObjFrom;                                          \
    return Clif_PyObjFrom(                                                 \
        src, clif_pybind11::PostConvFromReturnValuePolicyPack(rvpp));      \
  }                                                                        \
                                                                           \
  template <typename T = Type,                                             \
            std::enable_if_t<clif_pybind11::HasPyObjFrom<T*>(), int> = 0>  \
  static handle cast(const Type* src,                                      \
                     const ::clif_pybind11::rvp_or_rvpp& rvpp,             \
                     handle /* parent */) {                                \
    using ::clif::Clif_PyObjFrom;                                          \
    return Clif_PyObjFrom(                                                 \
        src, clif_pybind11::PostConvFromReturnValuePolicyPack(rvpp));      \
  }                                                                        \
                                                                           \
  template <typename T = Type,                                             \
            std::enable_if_t<clif_pybind11::HasPyObjFrom<T**>(), int> = 0> \
  static handle cast(Type** src, const ::clif_pybind11::rvp_or_rvpp& rvpp, \
                     handle /* parent */) {                                \
    using ::clif::Clif_PyObjFrom;                                          \
    return Clif_PyObjFrom(                                                 \
        src, clif_pybind11::PostConvFromReturnValuePolicyPack(rvpp));      \
  }

template <class Type, typename SFINAE = void>
struct clif_type_caster {
 public:
#if defined(PYBIND11_HAS_RETURN_VALUE_POLICY_PACK)
  PYBIND11_TYPE_CASTER_RVPP(Type, const_name<Type>());
#else
  PYBIND11_TYPE_CASTER(Type, const_name<Type>());
#endif

  CLIF_TYPE_CASTER_CAST

  template <class T = Type,
            std::enable_if_t<clif_pybind11::HasPyObjAs<T>(), int> = 0>
  bool load(handle src, bool) {
    using ::clif::Clif_PyObjAs;
    return ::clif::ClearClif_PyObjAsPythonErrorIfFalse(
        Clif_PyObjAs(src.ptr(), &value));
  }
};

template <class Type>
struct clif_type_caster<
    Type, typename std::enable_if_t<
              clif_pybind11::HasAbslOptionalPyObjAsFalseIfAbstract<Type>()>> {
 public:
  static constexpr auto name = const_name<Type>();

  CLIF_TYPE_CASTER_CAST

  bool load(handle src, bool) {
    using ::clif::Clif_PyObjAs;
    return ::clif::ClearClif_PyObjAsPythonErrorIfFalse(
        Clif_PyObjAs(src.ptr(), &value));
  }

  template <typename T_>
  using cast_op_type = movable_cast_op_type<T_>;

  operator Type*() { return &(value.value()); }
  operator Type&() { return value.value(); }
  operator Type&&() && { return std::move(value.value()); }

 private:
  std::optional<Type> value;
};

template <class Type>
struct clif_type_caster<
    Type, typename std::enable_if_t<
              !clif_pybind11::HasAbslOptionalPyObjAsFalseIfAbstract<Type>() &&
              clif_pybind11::HasPyObjAs<Type*>()>> {
 public:
  static constexpr auto name = const_name<Type>();

  CLIF_TYPE_CASTER_CAST

  template <class T = Type,
            std::enable_if_t<clif_pybind11::HasPyObjAs<T*>(), int> = 0>
  bool load(handle src, bool) {
    using ::clif::Clif_PyObjAs;
    return ::clif::ClearClif_PyObjAsPythonErrorIfFalse(
        Clif_PyObjAs(src.ptr(), &value));
  }

  template <typename T_>
  using cast_op_type = ::pybind11::detail::cast_op_type<T_>;

  operator Type*() { return value; }
  operator Type&() { return *value; }

 private:
  Type* value;
};

template <class Type>
struct clif_type_caster<
    Type, typename std::enable_if_t<
              !clif_pybind11::HasAbslOptionalPyObjAsFalseIfAbstract<Type>() &&
              !clif_pybind11::HasPyObjAs<Type*>() &&
              clif_pybind11::HasNonClifPyObjAs<std::unique_ptr<Type>>(0)>> {
 public:
  static constexpr auto name = const_name<Type>();

  CLIF_TYPE_CASTER_CAST

  template <
      class T = Type,
      std::enable_if_t<clif_pybind11::HasNonClifPyObjAs<std::unique_ptr<T>>(0),
                       int> = 0>
  bool load(handle src, bool) {
    // TODO: Test with two passes in pybind11 dispatcher.
    std::unique_ptr<Type> res;
    using ::clif::Clif_PyObjAs;
    if (!::clif::ClearClif_PyObjAsPythonErrorIfFalse(
            Clif_PyObjAs(src.ptr(), &res))) {
      return false;
    }
    value = std::move(res);
    return true;
  }

  template <typename T_>
  using cast_op_type = movable_cast_op_type<T_>;

  operator Type*() { return value.get(); }
  operator Type&() { return *value; }
  operator Type&&() && { return std::move(*value); }

 private:
  std::unique_ptr<Type> value;
};

template <class Type>
struct clif_type_caster<
    Type, typename std::enable_if_t<
              !clif_pybind11::HasAbslOptionalPyObjAsFalseIfAbstract<Type>() &&
              !clif_pybind11::HasPyObjAs<Type*>() &&
              !clif_pybind11::HasNonClifPyObjAs<std::unique_ptr<Type>>(0) &&
              clif_pybind11::HasPyObjAs<std::shared_ptr<Type>>()>> {
 public:
  static constexpr auto name = const_name<Type>();

  CLIF_TYPE_CASTER_CAST

  template <class T = Type,
            std::enable_if_t<clif_pybind11::HasPyObjAs<std::shared_ptr<Type>>(),
                             int> = 0>
  bool load(handle src, bool) {
    std::shared_ptr<Type> res;
    using ::clif::Clif_PyObjAs;
    if (!::clif::ClearClif_PyObjAsPythonErrorIfFalse(
            Clif_PyObjAs(src.ptr(), &res))) {
      return false;
    }
    value = std::move(res);
    return true;
  }

  template <typename T_>
  using cast_op_type = movable_cast_op_type<T_>;

  operator Type*() { return value.get(); }
  operator Type&() { return *value; }
  operator Type&&() && { return std::move(*value); }

 private:
  std::shared_ptr<Type> value;
};

template <class Type>
struct clif_type_caster<
    Type, typename std::enable_if_t<
              !clif_pybind11::HasAbslOptionalPyObjAsFalseIfAbstract<Type>() &&
              !clif_pybind11::HasPyObjAs<Type*>() &&
              !clif_pybind11::HasNonClifPyObjAs<std::unique_ptr<Type>>(0) &&
              !clif_pybind11::HasPyObjAs<std::shared_ptr<Type>>() &&
              std::is_abstract_v<Type>>> {
 public:
  static constexpr auto name = const_name<Type>();

  CLIF_TYPE_CASTER_CAST

  template <class T = Type,
            std::enable_if_t<clif_pybind11::HasPyObjAs<std::unique_ptr<T>>(),
                             int> = 0>
  bool load(handle src, bool) {
    std::unique_ptr<Type> res;
    using ::clif::Clif_PyObjAs;
    if (!::clif::ClearClif_PyObjAsPythonErrorIfFalse(
            Clif_PyObjAs(src.ptr(), &res))) {
      return false;
    }
    value = std::move(res);
    return true;
  }

  template <typename T_>
  using cast_op_type = movable_cast_op_type<T_>;

  operator Type*() { return value.get(); }
  operator Type&() { return *value; }
  operator Type&&() && { return std::move(*value); }

 private:
  std::unique_ptr<Type> value;
};

template <typename Type, typename HolderType>
struct clif_smart_ptr_type_caster {
 public:
  PYBIND11_TYPE_CASTER(HolderType, const_name<Type>());

  template <typename T = HolderType,
            std::enable_if_t<clif_pybind11::HasPyObjAs<T>(), int> = 0>
  bool load(handle src, bool) {
    using ::clif::Clif_PyObjAs;
    return ::clif::ClearClif_PyObjAsPythonErrorIfFalse(
        Clif_PyObjAs(src.ptr(), &value));
  }

  template <typename T = HolderType,
            std::enable_if_t<clif_pybind11::HasPyObjFrom<T>(), int> = 0>
  static handle cast(T src, return_value_policy /* policy */,
                     handle /* parent */) {
    using ::clif::Clif_PyObjFrom;
    return Clif_PyObjFrom(std::move(src), {});
  }
};

}  // namespace detail
}  // namespace pybind11

// NOTE: This macro MUST ONLY BE INVOKED IN THE GLOBAL NAMESPACE.
#define PYCLIF_PYBIND11_CLIF_TYPE_CASTERS(...)                        \
  namespace pybind11::detail {                                        \
  template <>                                                         \
  struct type_caster<__VA_ARGS__> : clif_type_caster<__VA_ARGS__> {}; \
  template <>                                                         \
  struct type_caster<std::shared_ptr<__VA_ARGS__>>                    \
      : clif_smart_ptr_type_caster<__VA_ARGS__,                       \
                                   std::shared_ptr<__VA_ARGS__>> {};  \
  template <>                                                         \
  struct type_caster<std::unique_ptr<__VA_ARGS__>>                    \
      : clif_smart_ptr_type_caster<__VA_ARGS__,                       \
                                   std::unique_ptr<__VA_ARGS__>> {};  \
  }

#endif  // CLIF_PYBIND11_CLIF_TYPE_CASTERS_H_
