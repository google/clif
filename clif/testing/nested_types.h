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
#ifndef CLIF_TESTING_NESTED_TYPES_H_
#define CLIF_TESTING_NESTED_TYPES_H_

struct Outer1 {
  struct Inner {
    int a;
  };
};

struct Outer2 {
  struct Inner {
    int b;
  };
};

struct Outer3 {
  enum Inner {
    k1 = 123,
    k2 = 234,
  };
};

struct Outer4 {
  enum MyInner {
    k1 = 321,
    k2 = 432
  };
};

struct Outer5 {
  enum Inner {
    k1 = 234,
    k2 = 567
  };
};

#endif  // CLIF_TESTING_NESTED_TYPES_H_
