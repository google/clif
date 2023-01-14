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
#ifndef THIRD_PARTY_CLIF_TESTING_OPTIONAL_H_
#define THIRD_PARTY_CLIF_TESTING_OPTIONAL_H_

#include <optional>

namespace clif_testing {
namespace optional {

struct DefaultConstructible {
  int a = 0;
};

struct NonDefaultConstructible {
  int a = 0;

  NonDefaultConstructible(int a) : a(a) {}

  static NonDefaultConstructible Make() { return NonDefaultConstructible{0}; }
};

inline std::optional<DefaultConstructible>
OptionalDefaultConstructibleRoundTrip(std::optional<DefaultConstructible> x) {
  return x;
}

inline std::optional<NonDefaultConstructible>
OptionalNonDefaultConstructibleRoundTrip(
    std::optional<NonDefaultConstructible> x) {
  return x;
}

}  // namespace optional
}  // namespace clif_testing

#endif  // THIRD_PARTY_CLIF_TESTING_OPTIONAL_H_
