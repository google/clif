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
#ifndef CLIF_TESTING_NESTED_FIELDS_H_
#define CLIF_TESTING_NESTED_FIELDS_H_

#include <memory>
#include <vector>

struct DD {
  int i;
};

struct CC {
  int i;
};

struct BB {
  CC c;
  DD d;

  DD GetD() {
    return d;
  }

  void SetD(const DD& dd) {
    d = dd;
  }
};

struct AA {
  BB b;
  CC c;
  DD* dp;
  std::unique_ptr<DD> du;
  std::shared_ptr<DD> ds;
  std::vector<int> v;
};

inline void ConsumeCC(std::unique_ptr<CC> up) { }
inline void ConsumeAA(std::unique_ptr<AA> up) { }

struct Base {
  int i;
};

struct Derived: public Base {
  int j;
};

#endif  // CLIF_TESTING_NESTED_FIELDS_H_
