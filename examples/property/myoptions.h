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
#ifndef CLIF_EXAMPLES_PROPERTY_MYOPTIONS_H_
#define CLIF_EXAMPLES_PROPERTY_MYOPTIONS_H_

#include <string>
#include <utility>

namespace clif_example {
namespace property {

class MyOptions {
 public:
  explicit MyOptions(std::string name) : name_(std::move(name)) {}

  void SetName(const std::string& n) {
    name_ = n;
  }

  std::string GetName() const {
    return name_;
  }

  void SetPath(const std::string& p) {
    path_ = p;
  }

  std::string GetPath() const {
    return path_;
  }

  void SetCount(int c) {
    count_ = c;
  }

  int GetCount() const {
    return count_;
  }

 private:
  std::string name_;
  std::string path_;
  int count_;
};

}  // namespace property
}  // namespace clif_example

#endif  // CLIF_EXAMPLES_PROPERTY_MYOPTIONS_H_
