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
#ifndef CLIF_TESTING_EXTEND_FROM_CLIFAUX_H_
#define CLIF_TESTING_EXTEND_FROM_CLIFAUX_H_

#include <string>
#include <string_view>

namespace clif_testing {
namespace extend_from_clifaux {

class WhatHappened {
 public:
  WhatHappened() : last_event_{"Nothing yet."} {}
  void Record(std::string_view event) const { last_event_ = event; }
  std::string Last() const { return last_event_; }

 private:
  mutable std::string last_event_;  // mutable for easy testing of const& self.
};

class ToBeRenamed : public WhatHappened {};

struct TestNestedMethod {
  struct Inner {
    Inner(int v) : value{v + 10} {}
    int value;

    Inner fine_with_unqualified_names(const Inner& other) {
      return Inner(100 * value + other.value);
    }
  };
};

struct WithTemplateMemberFunction {
  template <typename T>
  T GetDefaultConstructed() const {
    return T();
  }
};

}  // namespace extend_from_clifaux
}  // namespace clif_testing

#endif  // CLIF_TESTING_EXTEND_FROM_CLIFAUX_H_
