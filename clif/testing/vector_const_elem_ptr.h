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
#ifndef CLIF_TESTING_VECTOR_CONST_ELEM_PTR_H_
#define CLIF_TESTING_VECTOR_CONST_ELEM_PTR_H_

#include <vector>

namespace clif_testing {

class Elem {
 public:
  explicit Elem(int val = 0) : value(val) {}
  int value;
};

inline int sum_elem_ptr(std::vector<Elem*> elems) {
  int sum = 0;
  for (auto p : elems) {
    sum += p->value;
  }
  return sum;
}

inline int prod_const_elem_ptr(std::vector<const Elem*> elems) {
  int prod = 1;
  for (auto p : elems) {
    prod *= p->value;
  }
  return prod;
}

}  // namespace clif_testing

#endif  // CLIF_TESTING_VECTOR_CONST_ELEM_PTR_H_
