/*
 * Copyright 2020 Google LLC
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
#ifndef CLIF_EXAMPLES_UNIQUE_PTR_MEMBER_UNIQUE_PTR_MEMBER_H_
#define CLIF_EXAMPLES_UNIQUE_PTR_MEMBER_UNIQUE_PTR_MEMBER_H_

#include <memory>

namespace clif_examples {
namespace unique_ptr_member {

class pointee {  // NOT copyable.
 public:
  pointee() {}

  int get_int() const { return 213; }

 private:
  pointee(const pointee&) = delete;
  pointee(pointee&&) = delete;
  pointee& operator=(const pointee&) = delete;
  pointee& operator=(pointee&&) = delete;
};

class ptr_owner {
 public:
  explicit ptr_owner(std::unique_ptr<pointee> ptr) : ptr_(std::move(ptr)) {}

 private:
  std::unique_ptr<pointee> ptr_;
};

// Just to have a minimal example of a typical C++ pattern.
inline int cpp_pattern() {
  auto obj = std::make_unique<pointee>();
  int result = (obj ? 10 : 0);
  ptr_owner owner(std::move(obj));
  result += (obj ? 1 : 0);
  return result;
}

}  // namespace unique_ptr_member
}  // namespace clif_examples

#endif  // CLIF_EXAMPLES_UNIQUE_PTR_MEMBER_UNIQUE_PTR_MEMBER_H_
