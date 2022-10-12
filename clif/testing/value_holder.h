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

#ifndef THIRD_PARTY_CLIF_TESTING_VALUE_HOLDER_H_
#define THIRD_PARTY_CLIF_TESTING_VALUE_HOLDER_H_

#include <vector>
namespace clif_testing {

class ValueHolder {
 public:
  ValueHolder(): value(0) { }
  ValueHolder(int v): value(v) { }
  int value;
};

class ValueHolderList {
 public:
  ValueHolderList(): values{} { }
  void push(int v) { values.push_back(ValueHolder(v)); }
  std::vector<ValueHolder> get_values() { return values; }
 private:
  std::vector<ValueHolder> values;
};

class ValueHolderFromOnly {
 public:
  ValueHolderFromOnly(): value(0) { }
  ValueHolderFromOnly(int v): value(v) { }
  int value;
};

class ValueHolderAsOnly {
 public:
  ValueHolderAsOnly(): value(0) { }
  ValueHolderAsOnly(int v): value(v) { }
  int value;
};

class ValueHolderPybind11Ignore {
 public:
  ValueHolderPybind11Ignore(): value(0) { }
  ValueHolderPybind11Ignore(int v): value(v) { }
  int value;
};

template <typename T, typename R>
class ValueHolderTemplate {
 public:
  ValueHolderTemplate(): value(0) { }
  ValueHolderTemplate(int v): value(v) { }
  int value;
};

class ValueHolderWithPybind11TypeCaster {
 public:
  ValueHolderWithPybind11TypeCaster(): value(0) { }
  ValueHolderWithPybind11TypeCaster(int v): value(v) { }
  int value;
};

class ValueHolderAbstract {
 public:
  virtual ~ValueHolderAbstract() = default;
  virtual int get_value() const = 0;
  int value;
};

class ValueHolderConcrete : public ValueHolderAbstract {
 public:
  ValueHolderConcrete() { value = 0; }
  ValueHolderConcrete(int v) { value = v; }
  int get_value() const override {
    return value;
  }
};

}  // namespace clif_testing

#endif  // THIRD_PARTY_CLIF_TESTING_VALUE_HOLDER_H_
