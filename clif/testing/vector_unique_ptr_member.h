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
#ifndef CLIF_TESTING_VECTOR_UNIQUE_PTR_MEMBER_H_
#define CLIF_TESTING_VECTOR_UNIQUE_PTR_MEMBER_H_

#include <memory>
#include <vector>

namespace clif_testing_vector_unique_ptr_member {

struct DataType {};

// Reduced from a use case in the wild.
struct VectorOwner {
  static std::unique_ptr<VectorOwner> Create(std::size_t num_elems) {
    return std::unique_ptr<VectorOwner>(
        new VectorOwner(std::vector<std::unique_ptr<DataType>>(num_elems)));
  }

  std::size_t data_size() const { return data_.size(); }

 private:
  explicit VectorOwner(std::vector<std::unique_ptr<DataType>> data)
      : data_(std::move(data)) {}

  const std::vector<std::unique_ptr<DataType>> data_;
};

}  // namespace clif_testing_vector_unique_ptr_member

#endif  // CLIF_TESTING_VECTOR_UNIQUE_PTR_MEMBER_H_
