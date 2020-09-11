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
#ifndef CLIF_TESTING_IMPLICIT_CONVERSION_H_
#define CLIF_TESTING_IMPLICIT_CONVERSION_H_

namespace clif_implicit_conversion_test {

struct A {
  int a;
};

// Class B is implicitly convertible to A*.
class B {
 public:
  explicit B(int i) { t.a = i; }
  operator A*() { return &t; }

 private:
  A t;
};

// Tests for wrapping functions with implicit conversion for input parameters.
int Func(A* t) { return t->a; }

}  // namespace clif_implicit_conversion_test

#endif  // CLIF_TESTING_IMPLICIT_CONVERSION_H_
