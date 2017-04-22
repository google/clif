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

struct Abc {
  explicit Abc(uint8_t start, uint8_t end)
      : s(start), l(end < start? 0: end-start+1) {}
  int length() { return l; }
  char operator[](int i);

  uint8_t s, l;
};

bool operator==(Abc const& lhs, Abc const& rhs) {
  return lhs.l == rhs.l && lhs.s == rhs.s;
}
bool operator!=(Abc const& lhs, Abc const& rhs) {
  return lhs.l != rhs.l || lhs.s != rhs.s;
}
bool operator<(Abc const& lhs, Abc const& rhs) {
  return lhs.l < rhs.l || lhs.s < rhs.s;
}
char Abc::operator[](int i) { return i >= 0 && i <= l? s+i: 0; }

#endif  // CLIF_TESTING_OPERATORS_H_
