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
#ifndef CLIF_TESTING_TEMPLATE_ALIAS_H_
#define CLIF_TESTING_TEMPLATE_ALIAS_H_

#include <vector>

template <typename T = int>
using default_vector = std::vector<T>;

// Using such an alias bypass all type checks for T on the CLIF side and must
// be implemented here.
template <typename T>
using clif_vector = typename std::enable_if<std::is_same<T, int>::value,
                                            default_vector<>>::type;

void func_default_vector_input(default_vector<> s) {}

void func_default_vector_output(default_vector<>* s) { s->push_back(123); }

default_vector<> func_default_vector_return() {
  default_vector<> d;
  d.push_back(100);
  return d;
}

// In this example, the using-declared type "clif_vector<T>" or the underlying
// type "default_vector<>" are equivalent in C++ definition, which are both
// "vector<int>".
void func_clif_vector(clif_vector<int> c) {}

template<class T>
using signed_size_type = typename std::make_signed<T>::type;

inline signed_size_type<size_t> func_signed_size_type_output() {
  return 123;
}

#endif  // CLIF_TESTING_TEMPLATE_ALIAS_H_
