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
#ifndef CLIF_TESTING_PICKLE_COMPATIBILITY_H_
#define CLIF_TESTING_PICKLE_COMPATIBILITY_H_

#include <string>
#include <string_view>
#include <vector>

namespace clif_testing {

class StoreTwoUsingPostproc {
 public:
  StoreTwoUsingPostproc(int v0, int v1) : values{v0, v1} {}
  int Get(int i) const { return values[i & 0x1]; }
  const StoreTwoUsingPostproc& Self(int protocol) const { return *this; }

 private:
  std::vector<int> values;
};

class StoreTwoUsingExtend {
 public:
  StoreTwoUsingExtend(int v0, int v1) : values{v0, v1} {}
  int Get(int i) const { return values[i & 0x1]; }

 private:
  std::vector<int> values;
};

template <unsigned SerialNumber>
class StoreTwoWithState {
 public:
  StoreTwoWithState() : values{-1, -2}, state{"white"} {}
  StoreTwoWithState(int v0, int v1) : values{v0, v1}, state{"blank"} {}
  const std::vector<int>& GetInitArgs() const { return values; }
  const std::string& GetState() const { return state; }
  void SetState(std::string_view state) { this->state = state; }

 private:
  std::vector<int> values;
  std::string state;
};

}  // namespace clif_testing

#endif  // CLIF_TESTING_PICKLE_COMPATIBILITY_H_
