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
#ifndef CLIF_EXAMPLES_INHERITANCE_INHERITANCE_H_
#define CLIF_EXAMPLES_INHERITANCE_INHERITANCE_H_

namespace clif_example {
namespace inheritance {

class Base {
 public:
  explicit Base(int i) : i_(i) {}

  int GetBaseValue() {
    return i_;
  }

 private:
  int i_;
};

class Derived1 : public Base {
 public:
  explicit Derived1(int j) : Base(12345), j_(j) {}

  int GetDerivedValue() {
    return j_;
  }

 private:
  int j_;
};

class Derived2 : public Base {
 public:
  Derived2() : Base(12345), j_(54321) { }

  int GetDerivedValue() {
    return j_;
  }

 private:
  int j_;
};

}  // namespace inheritance
}  // namespace clif_example

#endif  // CLIF_EXAMPLES_INHERITANCE_INHERITANCE_H_
