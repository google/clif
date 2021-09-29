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

#include "third_party/pybind11/include/pybind11/smart_holder.h"

#include "clif/python/types.h"
// TODO: Avoid util/task/python/clif dependency.
#include "util/task/python/clif/status_casters.h"

#include <Python.h>

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

}  // namespace detail
}  // namespace pybind11

#endif  // THIRD_PARTY_CLIF_PYBIND11_TYPE_CASTERS_H_
