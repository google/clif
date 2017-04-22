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
#ifndef CLIF_EXAMPLES_WRAPMETHOD_WRAPMETHOD_H_
#define CLIF_EXAMPLES_WRAPMETHOD_WRAPMETHOD_H_

#include <memory>
#include <vector>

namespace clif_example {
namespace wrapmethod {

class ClassWithMethods {
 public:
  explicit ClassWithMethods(int size) : data_(size) { }

  ClassWithMethods(int size, int val) : data_(size, val) { }

  int Get(int index) {
    return data_.at(index);
  }

  void Set(int index, int v) {
    data_.at(index) = v;
  }

  int Size() {
    return data_.size();
  }

  void Delete(int index) {
    std::vector<int>::iterator iter = data_.begin();
    for (int i = 0; i < index; ++i) {
      ++iter;
    }
    data_.erase(iter);
  }

  static int GetStaticNumber() {
    return kStaticNumber;
  }

  static const int kStaticNumber;

 private:
  std::vector<int> data_;
};

}  // namespace wrapmethod
}  // namespace clif_example

#endif  // CLIF_EXAMPLES_WRAPMETHOD_WRAPMETHOD_H_
