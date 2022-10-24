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
#ifndef CLIF_TESTING_DEFAULT_ARGS_H_
#define CLIF_TESTING_DEFAULT_ARGS_H_

#include <memory>
#include <string>
#include <vector>

struct Arg {
  int e;
};

class MyClass {
 public:
  enum Enum {
    E1 = 321,
    E2 = 432,
    E3 = 543
  };

  enum Flag {
    F1 = 1,
    F2 = 2,
    F3 = 4,
    F5 = 8
  };

  int MethodWithDefaultClassArg(Arg arg = {10}, int i = 100) {
    return arg.e + i;
  }

  int MethodWithUnknownDefaultArg(int i, Arg arg = {10}) {
    return arg.e + i;
  }

  int MethodWithManyUnknownDefaultArgs(
      int a, Arg b = {2}, Arg c = {3}, Arg d = {4}, Arg e = {5},
      std::unique_ptr<Arg> ptr = nullptr, int f = 6) {
    int ptr_value = 0;
    if (ptr) {
      ptr_value = ptr->e;
    }
    return a + b.e + c.e + d.e + e.e + f + ptr_value;
  }

  int MethodWithMultipleUnknownDefaultArgs(
      int a, Arg b = {2}, Arg c = {3}, int d = 4) {
    return a + b.e + c.e + d;
  }

  int MethodWithKnownDefaultArgs(
      int a, int b = 2, Arg c = {3}, int d = 4) {
    return a + b + c.e + d;
  }

  int MethodWithUnKnownUniquePtrDefaultArg(
      int a, std::unique_ptr<Arg> b = nullptr, int c = 3, int d = 4) {
    int b_value = 0;
    if (b) {
      b_value = b->e;
    }
    return a + b_value + c + d;
  }

  std::string MethodWithUnknownDefaultArgLambdaExpression(
      int i, Arg arg = {10}) {
    return std::to_string(arg.e + i);
  }

  int MethodWithDefaultEnumArg(Enum e = kMyEnum, int i = 100) {
    return e + i;
  }

  int MethodWithDefaultPtrArg(Arg* arg = nullptr, int i = 100) {
    if (arg == nullptr) {
      return i;
    } else {
      return arg->e + i;
    }
  }

  int MethodWithDefaultFlag(int flag = F1 | F2, int i = 16) {
    return flag | i;
  }

  int MethodThrowAwayDefault(int input1 = 1, int input2 = 1) {
    return input1 + input2;
  }

  void MethodWithOutputDefault(int input = 1, int* output = nullptr) {
    if (output != nullptr) {
      *output = 1000;
    }
  }

 private:
  static const Enum kMyEnum;
};

const MyClass::Enum MyClass::kMyEnum = E2;

#endif  // CLIF_TESTING_DEFAULT_ARGS_H_
