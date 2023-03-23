/*
 * Copyright 2023 Google LLC
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
#ifndef CLIF_TESTING_RAW_POINTER_RETURN_MEMBER_FUNCTION_H_
#define CLIF_TESTING_RAW_POINTER_RETURN_MEMBER_FUNCTION_H_

#include <cstddef>
#include <vector>

namespace clif_testing_raw_pointer_return_member_function {

struct DataField {
  int int_value = -99;
};

struct DataFieldsHolder {
  std::vector<DataField> vec;

  DataFieldsHolder(std::size_t vec_size) {
    for (std::size_t i = 0; i < vec_size; i++) {
      vec.push_back(DataField{13 + static_cast<int>(i) * 11});
    }
  }

  DataField* vec_at(std::size_t index) {
    if (index >= vec.size()) {
      return nullptr;
    }
    return &vec[index];
  }
};

}  // namespace clif_testing_raw_pointer_return_member_function

#endif  // CLIF_TESTING_RAW_POINTER_RETURN_MEMBER_FUNCTION_H_
