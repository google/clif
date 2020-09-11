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
#ifndef CLIF_TESTING_PASS_NONE_H_
#define CLIF_TESTING_PASS_NONE_H_

#include <memory>

namespace clif_testing {

struct IntHolder {
  IntHolder(int value_) : value{value_} {}
  int value;
};

int pass_holder_by_value(IntHolder holder) { return holder.value * 3; }

int pass_const_ref_holder(const IntHolder& holder) { return holder.value * 5; }

int pass_const_ptr_holder(const IntHolder* holder) {
  if (holder == nullptr) {
    return 11;
  }
  return holder->value * 7;
}

int pass_shared_ptr_holder(std::shared_ptr<IntHolder> holder) {
  if (holder == nullptr) {
    return 17;
  }
  return holder->value * 13;
}

}  // namespace clif_testing

#endif  // CLIF_TESTING_PASS_NONE_H_
