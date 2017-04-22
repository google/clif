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
#ifndef CLIF_TESTING_IMPORTED_METHODS_H_
#define CLIF_TESTING_IMPORTED_METHODS_H_

namespace clif_testing {

class Base {
 public:
  explicit Base(int a) : a_(a) {}

 protected:
  int GetA(int offset) { return a_ + offset; }

 private:
  int a_;
};

class Derived : public Base {
 public:
  using Base::Base;

  using Base::GetA;

  int GetA() {
    return Base::GetA(0);
  }
};

}  // namespace clif_testing

#endif  // CLIF_TESTING_IMPORTED_METHODS_H_
