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

#ifndef CLIF_PYBIND11_TYPE_CASTERS_H_
#define CLIF_PYBIND11_TYPE_CASTERS_H_

// pybind11 includes have to be at the very top, even before Python.h
#include <pybind11/smart_holder.h>

// Must be after pybind11 include.
#include <Python.h>

#include <map>
#include <memory>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "absl/container/flat_hash_map.h"
#include "absl/container/flat_hash_set.h"
#include "clif/pybind11/status_return_override.h"
#include "clif/python/types.h"
#include "third_party/pybind11/include/pybind11/detail/common.h"
#include "third_party/pybind11_abseil/status_caster.h"
#include "third_party/pybind11_abseil/statusor_caster.h"

namespace pybind11 {
namespace detail {

template <>
struct type_caster<absl::int128> {
 public:
  PYBIND11_TYPE_CASTER(absl::int128, _("int128"));
  bool load(handle src, bool convert) {
    using ::clif::Clif_PyObjAs;
    return Clif_PyObjAs(src.ptr(), &value);
  }

  static handle cast(absl::int128 src, return_value_policy, handle) {
    using ::clif::Clif_PyObjFrom;
    return Clif_PyObjFrom(src, {});
  }
};

template <>
struct type_caster<absl::uint128> {
 public:
  PYBIND11_TYPE_CASTER(absl::uint128, _("uint128"));
  bool load(handle src, bool convert) {
    using ::clif::Clif_PyObjAs;
    return Clif_PyObjAs(src.ptr(), &value);
  }

  static handle cast(absl::uint128 src, return_value_policy, handle) {
    using ::clif::Clif_PyObjFrom;
    return Clif_PyObjFrom(src, {});
  }
};

#ifdef ABSL_HAVE_INTRINSIC_INT128
template <>
struct type_caster<__int128> {
 public:
  PYBIND11_TYPE_CASTER(__int128, _("int128"));
  bool load(handle src, bool convert) {
    using ::clif::Clif_PyObjAs;
    return Clif_PyObjAs(src.ptr(), &value);
  }

  static handle cast(__int128 src, return_value_policy, handle) {
    using ::clif::Clif_PyObjFrom;
    return Clif_PyObjFrom(src, {});
  }
};

template <>
struct type_caster<unsigned __int128> {
 public:
  PYBIND11_TYPE_CASTER(unsigned __int128, _("uint128"));
  bool load(handle src, bool convert) {
    using ::clif::Clif_PyObjAs;
    return Clif_PyObjAs(src.ptr(), &value);
  }

  static handle cast(unsigned __int128 src, return_value_policy, handle) {
    using ::clif::Clif_PyObjFrom;
    return Clif_PyObjFrom(src, {});
  }
};
#endif

template <typename ValueAndHolder, typename Value>
class smart_pointer_vector_caster {
  using value_conv = make_caster<Value>;

 public:
  PYBIND11_TYPE_CASTER(
      ValueAndHolder, const_name("List[") + value_conv::name + const_name("]"));

  bool load(handle src, bool convert) {
    if (isinstance<none>(src)) {
      value.reset();
      return true;
    }
    if (!isinstance<sequence>(src) || isinstance<bytes>(src) ||
      isinstance<str>(src)) {
      return false;
    }
    auto s = reinterpret_borrow<sequence>(src);
    value.reset(new std::vector<Value>);
    for (auto it : s) {
      value_conv conv;
      if (!conv.load(it, convert)) {
        return false;
      }
      value->push_back(cast_op<Value &&>(std::move(conv)));
    }
    return true;
  }

  static handle cast(ValueAndHolder src, return_value_policy policy,
                     handle parent) {
    if (!src) {
      return none();
    }
    list l(src->size());
    ssize_t index = 0;
    for (auto &&value : *src) {
      auto value_ = reinterpret_steal<object>(
          value_conv::cast(forward_like<Value>(value), policy, parent));
      if (!value_) {
        return handle();
      }
      PyList_SET_ITEM(
          l.ptr(), index++, value_.release().ptr());  // steals a reference
    }
    return l.release();
  }
};

template <typename T, typename D>
class type_caster<std::unique_ptr<std::vector<T>, D>>
    : public smart_pointer_vector_caster<
        std::unique_ptr<std::vector<T>, D>, T> {};

template <typename T>
class type_caster<std::shared_ptr<std::vector<T>>>
    : public smart_pointer_vector_caster<std::shared_ptr<std::vector<T>>, T> {};


template <typename ValueAndHolder, typename Type, typename Key, typename Value>
class smart_pointer_map_caster {
  using key_conv = make_caster<Key>;
  using value_conv = make_caster<Value>;

 public:
  PYBIND11_TYPE_CASTER(
      ValueAndHolder, const_name("Dict[") + key_conv::name + const_name(", ") +
      value_conv::name + const_name("]"));

  bool load(handle src, bool convert) {
    if (isinstance<none>(src)) {
      value.reset();
      return true;
    }
    if (!isinstance<dict>(src)) {
      return false;
    }
    auto d = reinterpret_borrow<dict>(src);
    value.reset(new Type);
    for (auto it : d) {
      key_conv kconv;
      value_conv vconv;
      if (!kconv.load(it.first.ptr(), convert) ||
          !vconv.load(it.second.ptr(), convert)) {
        return false;
      }
      value->emplace(cast_op<Key &&>(std::move(kconv)),
                     cast_op<Value &&>(std::move(vconv)));
    }
    return true;
  }

  static handle cast(ValueAndHolder src, return_value_policy policy,
                     handle parent) {
    if (!src) {
      return none();
    }
    dict d;
    return_value_policy policy_key = policy;
    return_value_policy policy_value = policy;
    for (auto &&kv : *src) {
      auto key = reinterpret_steal<object>(
          key_conv::cast(forward_like<Key>(kv.first), policy_key, parent));
      auto value = reinterpret_steal<object>(
          value_conv::cast(forward_like<Value>(kv.second), policy_value,
                           parent));
      if (!key || !value) {
        return handle();
      }
      d[key] = value;
    }
    return d.release();
  }
};

template <typename Key, typename Value, typename D, typename... Extra>
class type_caster<std::unique_ptr<std::map<Key, Value, Extra...>, D>>
    : public smart_pointer_map_caster<
        std::unique_ptr<std::map<Key, Value, Extra...>, D>,
        std::map<Key, Value, Extra...>, Key, Value> {};

template <typename Key, typename Value, typename... Extra>
class type_caster<std::shared_ptr<std::map<Key, Value, Extra...>>>
    : public smart_pointer_map_caster<
        std::shared_ptr<std::map<Key, Value, Extra...>>,
        std::map<Key, Value, Extra...>, Key, Value> {};

template <typename Key, typename Value, typename D, typename... Extra>
class type_caster<std::unique_ptr<std::unordered_map<Key, Value, Extra...>, D>>
    : public smart_pointer_map_caster<
        std::unique_ptr<std::unordered_map<Key, Value, Extra...>, D>,
        std::unordered_map<Key, Value, Extra...>, Key, Value> {};

template <typename Key, typename Value, typename... Extra>
class type_caster<std::shared_ptr<std::unordered_map<Key, Value, Extra...>>>
    : public smart_pointer_map_caster<
        std::shared_ptr<std::unordered_map<Key, Value, Extra...>>,
        std::unordered_map<Key, Value, Extra...>, Key, Value> {};

template <typename Key, typename Value, typename D, typename... Extra>
struct type_caster<std::unique_ptr<
                      absl::flat_hash_map<Key, Value, Extra...>, D>>
    : public smart_pointer_map_caster<
        std::unique_ptr<absl::flat_hash_map<Key, Value, Extra...>, D>,
        absl::flat_hash_map<Key, Value, Extra...>, Key, Value> {};

template <typename Key, typename Value, typename... Extra>
struct type_caster<std::shared_ptr<
                      absl::flat_hash_map<Key, Value, Extra...>>>
    : public smart_pointer_map_caster<
        std::shared_ptr<absl::flat_hash_map<Key, Value, Extra...>>,
        absl::flat_hash_map<Key, Value, Extra...>, Key, Value> {};

template <typename ValueAndHolder, typename Type, typename Key>
class smart_pointer_set_caster {
  using key_conv = make_caster<Key>;

 public:
  PYBIND11_TYPE_CASTER(
      ValueAndHolder, const_name("Set[") + key_conv::name + const_name("]"));

  bool load(handle src, bool convert) {
    if (isinstance<none>(src)) {
      value.reset();
      return true;
    }
    if (!isinstance<pybind11::set>(src)) {
      return false;
    }
    auto s = reinterpret_borrow<pybind11::set>(src);
    value.reset(new Type);
    for (auto entry : s) {
      key_conv conv;
      if (!conv.load(entry, convert)) {
        return false;
      }
      value->insert(cast_op<Key &&>(std::move(conv)));
    }
    return true;
  }

  static handle cast(ValueAndHolder src, return_value_policy policy,
                     handle parent) {
    if (!src) {
      return none();
    }
    pybind11::set s;
    for (auto &&value : *src) {
      auto value_ = reinterpret_steal<object>(
          key_conv::cast(forward_like<Key>(value), policy, parent));
      if (!value_ || !s.add(std::move(value_))) {
        return handle();
      }
    }
    return s.release();
  }
};

template <typename Key, typename D, typename... Extra>
class type_caster<std::unique_ptr<std::set<Key, Extra...>, D>>
    : public smart_pointer_set_caster<
        std::unique_ptr<std::set<Key, Extra...>, D>,
        std::set<Key, Extra...>, Key> {};

template <typename Key, typename... Extra>
class type_caster<std::shared_ptr<std::set<Key, Extra...>>>
    : public smart_pointer_set_caster<
        std::shared_ptr<std::set<Key, Extra...>>,
        std::set<Key, Extra...>, Key> {};

template <typename Key, typename D, typename... Extra>
class type_caster<std::unique_ptr<std::unordered_set<Key, Extra...>, D>>
    : public smart_pointer_set_caster<
        std::unique_ptr<std::unordered_set<Key, Extra...>, D>,
        std::unordered_set<Key>, Key> {};

template <typename Key, typename... Extra>
class type_caster<std::shared_ptr<std::unordered_set<Key, Extra...>>>
    : public smart_pointer_set_caster<
        std::shared_ptr<std::unordered_set<Key, Extra...>>,
        std::unordered_set<Key, Extra...>, Key> {};

template <typename Key, typename D, typename... Extra>
struct type_caster<
        std::unique_ptr<absl::flat_hash_set<Key, Extra...>, D>>
    : public smart_pointer_set_caster<
        std::unique_ptr<absl::flat_hash_set<Key, Extra...>, D>,
        absl::flat_hash_set<Key, Extra...>, Key> {};

template <typename Key, typename... Extra>
struct type_caster<std::shared_ptr< absl::flat_hash_set<Key, Extra...>>>
    : public smart_pointer_set_caster<
        std::shared_ptr<absl::flat_hash_set<Key, Extra...>>,
        absl::flat_hash_set<Key, Extra...>, Key> {};

template <typename ValueAndHolder>
class smart_pointer_string_caster {
  using StringCaster = make_caster<std::string>;
  StringCaster str_caster;

 public:
  PYBIND11_TYPE_CASTER(ValueAndHolder, const_name("str"));

  bool load(handle src, bool convert) {
    if (!str_caster.load(src, convert)) {
      return false;
    }
    value.reset(
        new std::string(cast_op<std::string &&>(std::move(str_caster))));
    return true;
  }

  static handle cast(ValueAndHolder src, return_value_policy policy,
                     handle parent) {
    return StringCaster::cast(*src, policy, parent);
  }
};

template <typename D>
struct type_caster<std::unique_ptr<std::string, D>>
    : public smart_pointer_string_caster<std::unique_ptr<std::string, D>> {};

template <>
struct type_caster<std::shared_ptr<std::string>>
    : public smart_pointer_string_caster<std::shared_ptr<std::string>> {};

}  // namespace detail
}  // namespace pybind11

#endif  // CLIF_PYBIND11_TYPE_CASTERS_H_
