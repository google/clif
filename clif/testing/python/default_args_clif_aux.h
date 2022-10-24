/*
 * Copyright 2022 Google LLC
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
#ifndef THIRD_PARTY_CLIF_TESTING_PYTHON_DEFAULT_ARGS_CLIF_AUX_H_
#define THIRD_PARTY_CLIF_TESTING_PYTHON_DEFAULT_ARGS_CLIF_AUX_H_

#include <memory>

#include "clif/testing/default_args.h"

inline int MyClass__extend__MethodWithManyUnknownDefaultArgsExtend(
    MyClass& self, int a, Arg b = {2}, Arg c = {3}, Arg d = {4},
    Arg e = {5}, std::unique_ptr<Arg> ptr = nullptr, int f = 6) {
  return self.MethodWithManyUnknownDefaultArgs(
      a, b, c, d, e, std::move(ptr), f);
}

inline int MethodWithManyUnknownDefaultArgsFree(
    int a, Arg b = {2}, Arg c = {3}, Arg d = {4},
    Arg e = {5}, std::unique_ptr<Arg> ptr = nullptr, int f = 6) {
  int ptr_value = 0;
  if (ptr) {
    ptr_value = ptr->e;
  }
  return a + b.e + c.e + d.e + e.e + f + ptr_value;
}

#endif  // THIRD_PARTY_CLIF_TESTING_PYTHON_DEFAULT_ARGS_CLIF_AUX_H_
