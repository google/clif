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

#ifndef THIRD_PARTY_CLIF_PYBIND11_TYPE_CASTERS_H_
#define THIRD_PARTY_CLIF_PYBIND11_TYPE_CASTERS_H_

#include <Python.h>

#include <map>
#include <memory>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#include "third_party/pybind11/include/pybind11/smart_holder.h"

#include "clif/python/types.h"
// TODO: Avoid util/task/python/clif dependency.
#include "util/task/python/clif/status_casters.h"


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

template <typename ValueAndHolder, typename Value>
class smart_pointer_vector_caster {
  using value_conv = make_caster<Value>;

 public:
  PYBIND11_TYPE_CASTER(
      ValueAndHolder, const_name("List[") + value_conv::name + const_name("]"));

  bool load(handle src, bool convert) {
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

template <typename T>
class type_caster<std::unique_ptr<std::vector<T>>>
    : public smart_pointer_vector_caster<std::unique_ptr<std::vector<T>>, T> {};

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

template <typename Key, typename Value>
class type_caster<std::unique_ptr<std::map<Key, Value>>>
    : public smart_pointer_map_caster<
        std::unique_ptr<std::map<Key, Value>>, std::map<Key, Value>, Key,
        Value> {};

template <typename Key, typename Value>
class type_caster<std::shared_ptr<std::map<Key, Value>>>
    : public smart_pointer_map_caster<
        std::shared_ptr<std::map<Key, Value>>, std::map<Key, Value>, Key,
        Value> {};

template <typename Key, typename Value>
class type_caster<std::unique_ptr<std::unordered_map<Key, Value>>>
    : public smart_pointer_map_caster<
        std::unique_ptr<std::unordered_map<Key, Value>>,
        std::unordered_map<Key, Value>, Key, Value> {};

template <typename Key, typename Value>
class type_caster<std::shared_ptr<std::unordered_map<Key, Value>>>
    : public smart_pointer_map_caster<
        std::shared_ptr<std::unordered_map<Key, Value>>,
        std::unordered_map<Key, Value>, Key, Value> {};

template <typename ValueAndHolder, typename Type, typename Key>
class smart_pointer_set_caster {
  using key_conv = make_caster<Key>;

 public:
  PYBIND11_TYPE_CASTER(
      ValueAndHolder, const_name("Set[") + key_conv::name + const_name("]"));

  bool load(handle src, bool convert) {
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

template <typename Key>
class type_caster<std::unique_ptr<std::set<Key>>>
    : public smart_pointer_set_caster<std::unique_ptr<std::set<Key>>,
                                      std::set<Key>, Key> {};

template <typename Key>
class type_caster<std::shared_ptr<std::set<Key>>>
    : public smart_pointer_set_caster<std::shared_ptr<std::set<Key>>,
                                      std::set<Key>, Key> {};

template <typename Key>
class type_caster<std::unique_ptr<std::unordered_set<Key>>>
    : public smart_pointer_set_caster<std::unique_ptr<std::unordered_set<Key>>,
                                      std::unordered_set<Key>, Key> {};

template <typename Key>
class type_caster<std::shared_ptr<std::unordered_set<Key>>>
    : public smart_pointer_set_caster<std::shared_ptr<std::unordered_set<Key>>,
                                      std::unordered_set<Key>, Key> {};

}  // namespace detail
}  // namespace pybind11

#endif  // THIRD_PARTY_CLIF_PYBIND11_TYPE_CASTERS_H_
