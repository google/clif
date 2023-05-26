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
#ifndef THIRD_PARTY_CLIF_TESTING_CLASSES_H_
#define THIRD_PARTY_CLIF_TESTING_CLASSES_H_

#include <string>
#include <utility>

// This comment intentionally includes UTF-8 characters as an IO test.
//   "Use pytype 🦆✔  - make code maintainers happy!"
namespace clif_testing {
namespace classes {

class K {
 public:
  explicit K(int i): i_(i) {}
  static const int C;
  int i1() const { return i_+1; }
  int get2() const { return i_*i_; }
  int get() const { return i_; }
  void set(int i) { i_ = i; }
  static int getCplus2() { return C+2; }
 private:
  int i_;
};

class NoDefaultConstructor {
 private:
  explicit NoDefaultConstructor() {}
 public:
  int A() { return 10; }
};

const int K::C = 1;

class Derived : public K {
 public:
  int j;
  explicit Derived(int i = 0) : K(i), j(i) {}
  Derived(int i0, int j0) : K(i0), j(j0) {}
  bool has(int k) {
    int i = get();
    if (i <= j) return i <= k && k <= j;
    return false;
  }
};

struct AddInit {
  int i = 567483;
  AddInit() = default;
  AddInit(const AddInit&) = default;
  AddInit(AddInit&&) = default;
  AddInit& operator=(const AddInit&) = default;
  AddInit& operator=(AddInit&&) = default;
};

class OverloadedGetterProperty {
 public:
  explicit OverloadedGetterProperty(int i): i_(i) {}
  int i() const { return i_; }
  void i(int value) { i_ = value; }
 private:
  int i_;
};

struct BytesAttributes {
  explicit BytesAttributes(const std::string& str_readonly):
      str_readonly_(str_readonly) {}
  std::string str_as_bytes;
  std::string str_as_str;

  std::string str_readonly_;
  std::string get_str_readonly() const { return str_readonly_; }
  std::string str_readwrite_;
  std::string get_str_readwrite() const { return str_readwrite_; }
  void set_str_readwrite(const std::string& v) { str_readwrite_ = v; }
};

enum SomeEnum {
  a = 1,
  b = -1,
};

struct ClassTakesEnum {
  explicit ClassTakesEnum(SomeEnum e = SomeEnum::a) {}
};

struct AddInitNoParams {
  explicit AddInitNoParams() {
    value = 10;
  }
  int get_value() { return value; }
  int value;
};

struct NestedAttributes {
  std::pair<std::string, std::string> pair_attr_str_str = {"foo", "bar"};
  std::pair<std::string, std::string> pair_attr_str_bytes = {"foo", "bar"};
  std::pair<std::string, std::string> pair_attr_bytes_str = {"foo", "bar"};
  std::pair<std::string, std::string> pair_attr_bytes_bytes = {"foo", "bar"};

  std::pair<std::string, std::string> pair_property_str_str = {"foo", "bar"};
  std::pair<std::string, std::string> pair_property_str_bytes = {"foo", "bar"};
  std::pair<std::string, std::string> pair_property_bytes_str = {"foo", "bar"};
  std::pair<std::string, std::string> pair_property_bytes_bytes = {"foo",
                                                                   "bar"};

  std::pair<std::string, std::string> pair_unproperty_str_str = {"foo", "bar"};
  std::pair<std::string, std::string> pair_unproperty_str_bytes = {"foo",
                                                                   "bar"};
  std::pair<std::string, std::string> pair_unproperty_bytes_str = {"foo",
                                                                   "bar"};
  std::pair<std::string, std::string> pair_unproperty_bytes_bytes = {"foo",
                                                                     "bar"};

  std::pair<std::string, std::string> get_pair_property_str_str() const {
    return pair_property_str_str;
  }

  void set_pair_property_str_str(const std::pair<std::string, std::string>& p) {
    pair_property_str_str = p;
  }

  std::pair<std::string, std::string> get_pair_property_str_bytes() const {
    return pair_property_str_bytes;
  }

  void set_pair_property_str_bytes(
      const std::pair<std::string, std::string>& p) {
    pair_property_str_bytes = p;
  }

  std::pair<std::string, std::string> get_pair_property_bytes_str() const {
    return pair_property_bytes_str;
  }

  void set_pair_property_bytes_str(
      const std::pair<std::string, std::string>& p) {
    pair_property_bytes_str = p;
  }

  std::pair<std::string, std::string> get_pair_property_bytes_bytes() const {
    return pair_property_bytes_bytes;
  }

  void set_pair_property_bytes_bytes(
      const std::pair<std::string, std::string>& p) {
    pair_property_bytes_bytes = p;
  }
};

// Use the duplicated namespace `clif_testing` for testing purposes.
namespace clif_testing {

struct WithAmbiguousNamespace {
  int get_value() { return 10; }
};

}  // namespace clif_testing

}  // namespace classes
}  // namespace clif_testing

#endif  // THIRD_PARTY_CLIF_TESTING_CLASSES_H_
