/*
 * Copyright 2023 Google LLC
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
#ifndef CLIF_TESTING_PROPERTY_PYTHON_MULTIPLE_INHERITANCE_H_
#define CLIF_TESTING_PROPERTY_PYTHON_MULTIPLE_INHERITANCE_H_

namespace clif_testing_python_multiple_inheritance {

struct CppBase {
  CppBase(int value) : base_value(value) {}
  int get_base_value() const { return base_value; }
  void reset_base_value(int new_value) { base_value = new_value; }

 private:
  int base_value;
};

struct CppDrvd : CppBase {
  CppDrvd(int value) : CppBase(value), drvd_value(value * 3) {}
  int get_drvd_value() const { return drvd_value; }
  void reset_drvd_value(int new_value) { drvd_value = new_value; }

  int get_base_value_from_drvd() const { return get_base_value(); }
  void reset_base_value_from_drvd(int new_value) {
    reset_base_value(new_value);
  }

 private:
  int drvd_value;
};

}  // namespace clif_testing_python_multiple_inheritance

#endif  // CLIF_TESTING_PYTHON_MULTIPLE_INHERITANCE_H_
