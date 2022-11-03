/*
 * Copyright 2022 Google LLC
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
#ifndef THIRD_PARTY_CLIF_TESTING_PYTHON_OPERATORS_CLIF_AUX_H_
#define THIRD_PARTY_CLIF_TESTING_PYTHON_OPERATORS_CLIF_AUX_H_

#include "clif/testing/operators.h"

namespace clif_ops_test {

inline int WithExtendGetItem_getitem(const WithExtendGetItem& obj, int i) {
  return obj.data[i];
}

inline int WithExtendGetItemAndExtendLen_len(
    const WithExtendGetItemAndExtendLen& obj) {
  return obj.data.size();
}

inline int WithExtendGetItemAndExtendLen_getitem(
    const WithExtendGetItemAndExtendLen& obj, int i) {
  return obj.data[i];
}

}  // namespace clif_ops_test

#endif  // THIRD_PARTY_CLIF_TESTING_PYTHON_OPERATORS_CLIF_AUX_H_
