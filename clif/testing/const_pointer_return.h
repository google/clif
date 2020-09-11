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
#ifndef CLIF_TESTING_CONST_POINTER_RETURN_H_
#define CLIF_TESTING_CONST_POINTER_RETURN_H_

namespace const_pointer_return {

class Pod {
 public:
  explicit Pod(int i) : x_(i) {}
  int get_x() { return x_; }
  void set_x(int i) { x_ = i; }

 private:
  int x_;
};

class MyClass {
 public:
  MyClass(int i, int value) : pod_(i), value_(value) {}
  const Pod* get_pod_ptr() const { return &pod_; }
  const int* get_int_ptr() { return &value_; }

 private:
  Pod pod_;
  int value_;
};

class NoCopy {
 public:
  explicit NoCopy(int i) : x_(i) {}
  NoCopy(const NoCopy&) = delete;
  NoCopy(NoCopy&&) = delete;
  NoCopy& operator=(const NoCopy&) = delete;
  NoCopy& operator=(NoCopy&&) = delete;
  int get_x() { return x_; }
  void set_x(int i) { x_ = i; }

 private:
  int x_;
};

class MyClass2 {
 public:
  explicit MyClass2(int i) : pod1_(i), pod2_(2 * i), nc_(i) {}
  // When both of the const and non-const overloading methods exist, Clif
  // selects the non-const candidate.
  const Pod* get_pod_ptr() const { return &pod1_; }
  Pod* get_pod_ptr() { return &pod2_; }
  const NoCopy* get_no_copy() const { return &nc_; }
  NoCopy* get_no_copy() { return &nc_; }

 private:
  Pod pod1_;
  Pod pod2_;
  NoCopy nc_;
};

}  // namespace const_pointer_return

#endif  // CLIF_TESTING_CONST_POINTER_RETURN_H_
