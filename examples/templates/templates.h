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
#ifndef CLIF_EXAMPLES_TEMPLATES_TEMPLATES_H_
#define CLIF_EXAMPLES_TEMPLATES_TEMPLATES_H_

namespace clif_example {
namespace templates {

template <typename A, typename B>
class MyClass {
 public:
  A GetA() {
    return a_;
  }

  B GetB() {
    return b_;
  }

  void SetA(A o) {
    a_ = o;
  }

  void SetB(B o) {
    b_ = o;
  }

 private:
  A a_;
  B b_;
};

template <typename A, typename B>
double MyAdd(A a, B b) {
  return a + b;
}

// Cannot be wrapped using Clif as the template argument for C cannot be
// deduced from the function arguments.
template <typename A, typename B, typename C>
C MyMul(A a, B b) {
  return a * b;
}

}  // namespace templates
}  // namespace clif_example

#endif  // CLIF_EXAMPLES_TEMPLATES_TEMPLATES_H_
