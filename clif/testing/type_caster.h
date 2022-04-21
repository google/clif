/*
 * Copyright 2021 Google LLC
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

#ifndef THIRD_PARTY_CLIF_TESTING_TYPE_CASTER_H_
#define THIRD_PARTY_CLIF_TESTING_TYPE_CASTER_H_

#include <Python.h>

#include <memory>
#include <optional>
#include <variant>
#include <vector>

#include "clif/testing/value_holder.h"

namespace clif_testing {

inline int get_value_direct(const ValueHolder& vh) {
  return vh.value;
}

inline int get_value_optional(const std::optional<ValueHolder>& vh) {
  if (vh.has_value()) {
    return vh.value().value;
  } else{
    return 0;
  }
}

inline int get_value_variant(const std::variant<ValueHolder>& vh) {
  return std::get<0>(vh).value;
}

inline ValueHolder return_value(int v) {
  return ValueHolder(v);
}

inline std::vector<ValueHolder> return_value_list(
    const std::vector<int>& values) {
  ValueHolderList res{};
  for (int value : values) {
    res.push(value);
  }
  return res.get_values();
}

inline ValueHolderFromOnly return_value_pyobjfrom_only(int v) {
  return ValueHolderFromOnly(v);
}

inline int get_value_pyobjas_only(const ValueHolderAsOnly& vh) {
  return vh.value;
}

inline int get_value_pybind11_ignore(const ValueHolderPybind11Ignore& vh) {
  return vh.value;
}

inline std::vector<PyObject *> pyobject_round_trip(
    const std::vector<PyObject*> vec) {
  return vec;
}

}  // namespace clif_testing

#endif  // THIRD_PARTY_CLIF_TESTING_TYPE_CASTER_H_
