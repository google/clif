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
#ifndef CLIF_TESTING_EXTEND_INIT_H_
#define CLIF_TESTING_EXTEND_INIT_H_

namespace clif_testing {

struct TestCase1 {
  TestCase1(): value(0) {}
  int get_value() { return value; }
  void set_value(int v) { value = v; }
  int value;
};

struct TestCase2 {
  TestCase2(): v1(0), v2(0), v3(0) {}
  int get_i() { return v1; }
  void set_i(int i) { v1 = i; }
  int get_j() { return v2; }
  void set_j(int j) { v2 = j; }
  int get_k() { return v3; }
  void set_k(int k) { v3 = k; }
  int v1, v2, v3;
};

struct TestCase3 {
  TestCase3(): value(0) {}
  int get_value() { return value; }
  void set_value(int v) { value = v; }
  int value;
};

struct TestNoDefaultConstructor {
  TestNoDefaultConstructor(int v): value(v) {}
  int get_value() { return value; }
  void set_value(int v) { value = v; }
  int value;
};

struct TestNestedInit {
  struct Inner {
    int get_value() { return value; }
    int value = -99;
  };
};

struct TestPyErrFromConstructor {};

}  // namespace clif_testing

#endif  // CLIF_TESTING_EXTEND_INIT_H_
