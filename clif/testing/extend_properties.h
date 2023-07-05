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
#ifndef CLIF_TESTING_EXTEND_PROPERTIES_H_
#define CLIF_TESTING_EXTEND_PROPERTIES_H_

#include <string>
#include <string_view>

namespace clif_testing {

struct ValueHolder {
  ValueHolder(int v): value_(v) {}
  int get_value() { return value_; }
  void set_value(int v) { value_ = v; }
  std::string get_value_str() { return value_str_; }
  void set_value_str(std::string_view v) { value_str_ = v; }
  int value_;
  std::string value_str_;
};

struct PropertyHolder {
  PropertyHolder(int v): value_holder_(v) {}
  ValueHolder value_holder_;
};

struct NestedPropertyHolder {
  struct Inner {
    Inner(int v) : value_holder_{v + 93} {}
    ValueHolder value_holder_;
  };
};

struct UncopyableHolder {
  explicit UncopyableHolder(int v): value(v) { }
  UncopyableHolder(const UncopyableHolder&) = delete;
  UncopyableHolder(UncopyableHolder&& other) { value = other.value; }

  UncopyableHolder& operator=(const UncopyableHolder &) = delete;
  UncopyableHolder& operator=(UncopyableHolder&& other) {
    value = other.value;
    return *this;
  }
  int get_value() { return value; }
  void set_value(int v) { value = v; }
  int value;
};

}  // namespace clif_testing

#endif  // CLIF_TESTING_EXTEND_PROPERTIES_H_
