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
#ifndef THIRD_PARTY_CLIF_TESTING_PYTHON_EXTEND_INIT_CLIF_AUX_H_
#define THIRD_PARTY_CLIF_TESTING_PYTHON_EXTEND_INIT_CLIF_AUX_H_

#include <Python.h>

#include <memory>

#include "clif/testing/extend_init.h"

namespace clif_testing {

inline std::unique_ptr<TestCase1> TestCase1__extend__init__(int v) {
  auto res = std::make_unique<TestCase1>();
  res->value = v;
  return res;
}

inline std::unique_ptr<TestCase2> TestCase2__extend__init__(
    int i, int j, int k) {
  auto res = std::make_unique<TestCase2>();
  res->v1 = i;
  res->v2 = j;
  res->v3 = k;
  return res;
}

inline std::unique_ptr<TestCase3> TestCase3__extend__init__(int v) {
  // Test with nullptr unique_ptr
  return nullptr;
}

inline std::unique_ptr<TestNoDefaultConstructor>
TestNoDefaultConstructor__extend__init__() {
  auto res = std::make_unique<TestNoDefaultConstructor>(0);
  return res;
}

inline std::unique_ptr<TestNestedInit::Inner>
TestNestedInit_Inner__extend__init__(int v) {
  auto res = std::make_unique<TestNestedInit::Inner>();
  res->value = v + 102;
  return res;
}

inline std::unique_ptr<TestPyErrFromConstructor>
TestPyErrFromConstructor__extend__init__(int v) {
  if (v == 0) {
    return std::make_unique<TestPyErrFromConstructor>();
  }
  PyErr_SetString(PyExc_ValueError, "RaisedFromExtendInit");
  return nullptr;
}

}  // namespace clif_testing

#endif  // THIRD_PARTY_CLIF_TESTING_PYTHON_EXTEND_INIT_CLIF_AUX_H_
