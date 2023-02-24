/*
 * Copyright 2017 Google Inc.
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
#ifndef CLIF_TESTING_SLOTS_H_
#define CLIF_TESTING_SLOTS_H_

#include <array>
#include <numeric>
#include <vector>

namespace clif_test_slots {

template<typename T, std::size_t N>
class Array {
 public:
  Array() { v_.fill(T()); }
  std::size_t Size() const { return N; }
  T const& Get(int index) { return v_[index]; }
  void Put(int index, T const& value) { v_[index] = value; }
  std::size_t Hash() const {
    if (v_[0] == 999) {  // Magic value to trigger special case.
      return std::numeric_limits<std::size_t>::max();
    }
    return std::accumulate(v_.begin(), v_.end(), T(0));
  }
 protected:
  std::array<T, N> v_;
};

template<std::size_t N>
using IntArray = Array<int, N>;

struct IntArray5 : IntArray<5> {
  void SetAll(int all_equal) { v_.fill(all_equal); }
  void Empty(int index) { v_[index] = 0; }
  std::vector<int> UnHashable() const {
    return std::vector<int>(v_.begin(), v_.end());
  }
};
}  // namespace clif_test_slots

#endif  // CLIF_TESTING_SLOTS_H_
