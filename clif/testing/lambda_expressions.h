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
#ifndef THIRD_PARTY_CLIF_TESTING_LAMBDA_EXPRESSIONS_H_
#define THIRD_PARTY_CLIF_TESTING_LAMBDA_EXPRESSIONS_H_

#include <string>

namespace clif_testing {

struct Abstract {
  virtual int get() = 0;
  virtual ~Abstract() { }
  int value = 0;
};

struct Derived: public Abstract {
  Derived(int v) { value = v; }
  int get() override {
    return value;
  }
};

struct NoCopyNoMove {
  NoCopyNoMove() : value(0) {}
  NoCopyNoMove(const NoCopyNoMove&) = delete;
  NoCopyNoMove(NoCopyNoMove&&) = delete;

  NoCopyNoMove& operator=(const NoCopyNoMove&) = delete;
  NoCopyNoMove& operator=(NoCopyNoMove&&) = delete;
  int value;
};

inline std::string abstract_reference_param(Abstract& obj) {
  return "abstract_reference";
}

inline std::string abstract_pointer_param(Abstract* obj) {
  return "abstract_pointer";
}

inline std::string nocopy_nomove_reference_param(const NoCopyNoMove&) {
  return "nocopy_nomove_reference";
}

inline std::string nocopy_nomove_pointer_param(NoCopyNoMove*) {
  return "nocopy_nomove_pointer";
}

inline std::string unique_pointer_param(std::unique_ptr<Abstract>) {
  return "unique_ptr";
}

}  // namespace clif_testing

#endif  // THIRD_PARTY_CLIF_TESTING_LAMBDA_EXPRESSIONS_H_
