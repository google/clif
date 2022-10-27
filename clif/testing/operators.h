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
#ifndef CLIF_TESTING_OPERATORS_H_
#define CLIF_TESTING_OPERATORS_H_
#include <stdint.h>
#include <stdlib.h>

namespace clif_ops_test {

struct Abc {
  explicit Abc(uint8_t start, uint8_t end)
      : s(start), l(end < start ? 0 : end-start+1) {}
  int length() { return l; }
  uint8_t operator[](int i);

  operator bool() const {
    return false;
  }

  operator int() const {
    return 1;
  }

  operator float() const {
    float a = 1.1;
    return a;
  }

  Abc& operator +=(int inc) {
    s += inc;
    return *this;
  }

  uint8_t s, l;
};

inline int operator*(const Abc& a) { return 1; }

inline bool operator==(Abc const& lhs, Abc const& rhs) {
  return lhs.l == rhs.l && lhs.s == rhs.s;
}
inline bool operator!=(Abc const& lhs, Abc const& rhs) {
  return !(lhs == rhs);
}
inline bool operator<(Abc const& lhs, Abc const& rhs) {
  return lhs.l < rhs.l || lhs.s < rhs.s;
}
inline bool operator>(Abc const& lhs, Abc const& rhs) {
  return rhs < lhs;
}
inline bool operator<=(Abc const& lhs, Abc const& rhs) {
  return !(rhs < lhs);
}
inline bool operator>=(Abc const& lhs, Abc const& rhs) {
  return !(lhs < rhs);
}
inline uint8_t Abc::operator[](int i) { return (i >= 0 && i < l) ? s+i : 0; }

// Check if |c| belongs to |abc| container.
// It should be a non-member function to test that it can be wrapped in class.
inline bool Abc_has(Abc const& abc, uint8_t c) {
  const int offset = c - abc.s;
  return offset >= 0 && offset < abc.l;
}


struct Num {
  int operator+(int) const { return 2; }
};
inline int operator%(const Num& a, int) { return 1; }
inline int operator%(int, const Num& a) { return 2; }
inline int operator-(int, const Num& a) { return 3; }

}  // namespace clif_ops_test

#endif  // CLIF_TESTING_OPERATORS_H_

