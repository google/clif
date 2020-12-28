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
#ifndef THIRD_PARTY_CLIF_TESTING_SUPRESS_UPCASTS_H_
#define THIRD_PARTY_CLIF_TESTING_SUPRESS_UPCASTS_H_

namespace clif_testing {

class BaseWrapper {
 private:
  class Base {
   public:
    virtual int value() { return 10; }
    virtual ~Base() {}
  };
  friend class DerivedSupressUpcasts;
};

class DerivedSupressUpcasts: public BaseWrapper::Base {
 public:
  int value() override {
    return 20;
  }
};

}  // namespace clif_testing

#endif  // THIRD_PARTY_CLIF_TESTING_SUPRESS_UPCASTS_H_
