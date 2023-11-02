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
#ifndef CLIF_TESTING_PYTHON_EXTEND_PROPERTIES_CLIF_AUX_H_
#define CLIF_TESTING_PYTHON_EXTEND_PROPERTIES_CLIF_AUX_H_

#include <string>
#include <string_view>

#include "clif/testing/extend_properties.h"

namespace clif_testing {
namespace extend_properties {

inline int ValueHolderPlain__extend__get_value_times_2(ValueHolder& self) {
  return self.get_value() * 2;
}

inline void ValueHolderPlain__extend__set_value_times_3(ValueHolder& self,
                                                        int value) {
  return self.set_value(value * 3);
}

inline int ValueHolderFinal__extend__get_value_times_4(ValueHolderFinal& self) {
  return self.get_value() * 4;
}

inline void ValueHolderFinal__extend__set_value_times_5(ValueHolderFinal& self,
                                                        int value) {
  return self.set_value(value * 5);
}

inline int ValueHolderImplicitGetPlain__extend__value(
    ValueHolderImplicitGetPlain& self) {
  return self.value() * 6;
}

inline void ValueHolderImplicitGetPlain__extend__set_value(
    ValueHolderImplicitGetPlain& self, int value) {
  return self.set_value(value * 7);
}

inline int ValueHolderImplicitGetFinal__extend__value(
    ValueHolderImplicitGetFinal& self) {
  return self.value() * 8;
}

inline void ValueHolderImplicitGetFinal__extend__set_value(
    ValueHolderImplicitGetFinal& self, int value) {
  return self.set_value(value * 9);
}

inline int PropertyHolder__extend__get_value(PropertyHolder& self) {
  return self.value_holder_.get_value();
}

inline int PropertyHolder__extend__get_value_times_ten(PropertyHolder& self) {
  return self.value_holder_.get_value() * 10;
}

inline int PropertyHolder__extend__get_value_gs(PropertyHolder& self) {
  return self.value_holder_.get_value();
}

inline void PropertyHolder__extend__set_value_gs(
    PropertyHolder& self, int value) {
  self.value_holder_.set_value(value);
}

inline int PropertyHolder__extend__get_value_ptr_self(PropertyHolder* self) {
  return self->value_holder_.get_value();
}

inline std::string PropertyHolder__extend__get_value_bytes(
    PropertyHolder& self) {
  return self.value_holder_.get_value_str();
}

inline void PropertyHolder__extend__set_value_bytes(
    PropertyHolder& self, std::string_view value) {
  self.value_holder_.set_value_str(value);
}

inline int NestedPropertyHolder_Inner__extend__get_value(
    NestedPropertyHolder::Inner& self) {
  return self.value_holder_.get_value() + 72;
}


inline int NestedPropertyHolder_Inner__extend__get_value_gs(
    NestedPropertyHolder::Inner& self) {
  return self.value_holder_.get_value() + 24;
}

inline void NestedPropertyHolder_Inner__extend__set_value_gs(
    NestedPropertyHolder::Inner& self, int value) {
  self.value_holder_.set_value(value + 57);
}

inline int UncopyableHolder__extend__get_value(UncopyableHolder& self) {
  return self.get_value();
}

inline void UncopyableHolder__extend__set_value(
    UncopyableHolder& self, int value) {
  self.set_value(value);
}

}  // namespace extend_properties
}  // namespace clif_testing

#endif  // CLIF_TESTING_PYTHON_EXTEND_PROPERTIES_CLIF_AUX_H_
