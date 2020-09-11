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
#ifndef THIRD_PARTY_CLIF_TESTING_CALL_METHOD_H_
#define THIRD_PARTY_CLIF_TESTING_CALL_METHOD_H_

namespace clif_testing {

class AddConstant {
 public:
  double base;
  AddConstant(double b): base(b) {}
  double operator()() const {
    return base + 1;
  }
};

class AddOneNumber {
 public:
  double base;
  AddOneNumber(double b): base(b) {}
  double operator()(double x1) const {
    return base + x1;
  }
};

class AddTwoNumbers {
 public:
  double base;
  AddTwoNumbers(double b): base(b) {}
  double operator()(double x1, double x2) const {
    return base + x1 + x2;
  }
};

class AddConstantInplace {
 public:
  double base;
  AddConstantInplace(double b): base(b) {}
  void operator()() {
    base += 1;
  }
};

class AddOneNumberInplace {
 public:
  double base;
  AddOneNumberInplace(double b): base(b) {}
  void operator()(double x1) {
    base += x1;
  }
};

class AddTwoNumbersInplace {
 public:
  double base;
  AddTwoNumbersInplace(double b): base(b) {}
  void operator()(double x1, double x2) {
    base = base + x1 + x2;
  }
};

}  // namespace clif_testing

#endif  // THIRD_PARTY_CLIF_TESTING_CALL_METHOD_H_
