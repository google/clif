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
#ifndef CLIF_TESTING_VIRTUAL_DERIVED_BEFORE_BASE_H_
#define CLIF_TESTING_VIRTUAL_DERIVED_BEFORE_BASE_H_

namespace clif_testing {

class Base {
 public:
  virtual ~Base() = default;
  virtual int Get() const = 0;
};

class Derived : public Base {
 public:
  explicit Derived(int i) : i_(i) {}
  int Get() const { return i_; }

 private:
  int i_;
};

}  // namespace clif_testing

#endif  // CLIF_TESTING_VIRTUAL_DERIVED_BEFORE_BASE_H_
