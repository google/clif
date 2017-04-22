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
#ifndef CLIF_TESTING_T3_H_
#define CLIF_TESTING_T3_H_

#include <string>

enum OldGlobalE {
  kTop1 = 1,
  kTopN = -1,
};


enum class NewGlobalE {
  TOP = 1000,
  BOTTOM = 1,
};


namespace some {

enum OldSomeE {
  kMy1 = 1,
  kMy2,
};
static_assert(kMy2 == 2, "enum value not incremented");


enum class NewSomeE {
  NEW
};


class K {
 public:
  typedef
  enum _e {
    kOne = 1,
  } e;

  enum class E {
    kOne = 11,
    kTwo = 12,
  };

  struct O {
    string n;
    bool f;
  };

  int i_;

  static K K2() { return K(); }

  void M(e i) { i_ = i; }
};

}  // namespace some

#endif  // CLIF_TESTING_T3_H_
