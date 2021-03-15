/*
 * Copyright 2021 Google LLC
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
#ifndef CLIF_TESTING_VIRTUAL_PY_CPP_MIX_H_
#define CLIF_TESTING_VIRTUAL_PY_CPP_MIX_H_

#include <memory>

namespace clif_testing_virtual_py_cpp_mix {

class Base {
 public:
  virtual ~Base() = default;
  virtual int Get() const { return 101; }
};

class CppDerived : public Base {
 public:
  int Get() const override { return 212; }
};

inline int GetFromCppPlaincPtr(const Base* b) { return b->Get() + 4000; }

inline int GetFromCppUniquePtr(std::unique_ptr<Base> b) {
  return b->Get() + 5000;
}

}  // namespace clif_testing_virtual_py_cpp_mix

#endif  // CLIF_TESTING_VIRTUAL_PY_CPP_MIX_H_
