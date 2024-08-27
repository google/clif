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

#include "clif/pybind11/clif_type_casters.h"

#include <vector>

#include "clif/pybind11/status_return_override.h"
#include "clif/python/postconv.h"
#include "clif/python/types.h"

namespace clif_pybind11 {

clif::py::PostConv PostConvFromReturnValuePolicyPack(const rvp_or_rvpp& rvpp) {
#if defined(PYBIND11_HAS_RETURN_VALUE_POLICY_PACK)
  if (rvpp.vec_rvpp.empty()) {
    auto policy = pybind11::return_value_policy(rvpp);
    if (policy == pybind11::return_value_policy::_return_as_bytes) {
      return clif::py::postconv::PASS;
    } else {
      return clif::UnicodeFromBytesIfPossible;
    }
  }
  std::vector<clif::py::PostConv> post_conv;
  for (auto& child_rvpp : rvpp.vec_rvpp) {
    post_conv.push_back(PostConvFromReturnValuePolicyPack(child_rvpp));
  }
  return clif::py::PostConv(post_conv);
#else
  return clif::UnicodeFromBytesIfPossible;
#endif
}

}  // namespace clif_pybind11
