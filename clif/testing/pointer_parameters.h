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
#ifndef THIRD_PARTY_CLIF_TESTING_POINTER_PARAMETERS_H_
#define THIRD_PARTY_CLIF_TESTING_POINTER_PARAMETERS_H_

#include <memory>
#include <utility>

namespace clif_testing {

inline void multiple_outputs_free_function(
    int input1, int input2, int input3, int* output1 = nullptr,
    int* output2 = nullptr, int* output3 = nullptr) {
  *output1 = 1000 + input1;
  *output2 = 1000 + input2;
  *output3 = 1000 + input3;
}

template <typename T>
class PointerHolder {
 public:
  PointerHolder(std::unique_ptr<int> p): ptr(std::move(p)) { }
  int get() { return *ptr; }
 private:
  std::unique_ptr<int> ptr;
};

class MyClass {
 public:
  void no_input(int* output = nullptr) {
    *output = 1000;
  }

  int pointer_input(int* inp = nullptr) {
    *inp += 1000;
    return *inp;
  }

  void one_input(int input, int* output = nullptr) {
    *output = 1000 + input;
  }

  void multiple_inputs(int input1, int input2, int input3,
                       int* output = nullptr) {
    *output = 1000 + input1 + input2 + input3;
  }

  void multiple_outputs(int input1, int input2, int input3,
                        int* output1 = nullptr, int* output2 = nullptr,
                        int* output3 = nullptr) {
    *output1 = 1000 + input1;
    *output2 = 1000 + input2;
    *output3 = 1000 + input3;
  }

  PointerHolder<std::unique_ptr<int>> unique_ptr_return(
      int input, int* output1 = nullptr) {
    *output1 = 1000 + input;
    auto ptr = std::make_unique<int>(10);
    PointerHolder<std::unique_ptr<int>> result(std::move(ptr));
    return result;
  }


  static void static_function(int input, int* output = nullptr) {
    *output = 1000 + input;
  }

  int multiple_outputs_and_int_return(
      int input1, int input2, int input3, int* output1 = nullptr,
      int* output2 = nullptr, int* output3 = nullptr) {
    *output1 = 1000 + input1;
    *output2 = 1000 + input2;
    *output3 = 1000 + input3;
    return 1000 + input1 + input2 + input3;
  }
};

}  // namespace clif_testing

#endif  // THIRD_PARTY_CLIF_TESTING_POINTER_PARAMETERS_H_
