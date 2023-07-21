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
#ifndef THIRD_PARTY_CLIF_TESTING_LAMBDA_EXPRESSIONS_H_
#define THIRD_PARTY_CLIF_TESTING_LAMBDA_EXPRESSIONS_H_

#include <Python.h>

#include <memory>
#include <set>
#include <string>
#include <string_view>
#include <vector>
#include <unordered_set>

namespace clif_testing {

enum SomeEnum {
  first = 1,
  second = -1,
};

struct Abstract {
  virtual int get() = 0;
  virtual ~Abstract() { }
  int value = 0;
};

struct Derived: public Abstract {
  explicit Derived(int v) { value = v; }
  int get() override {
    return value;
  }
};

struct NoCopy {
  // This constructor is to resolve Github CI failures.
  NoCopy() : value("Default") { }
  explicit NoCopy(std::string_view v) : value(v) {}
  NoCopy(const NoCopy&) = delete;
  NoCopy(NoCopy&& other) { value = other.value; }

  NoCopy& operator=(const NoCopy&) = delete;
  NoCopy& operator=(NoCopy&& other) {
    value = other.value;
    return *this;
  }
  std::string value;
  std::string get() { return value; }
};

struct NoCopyNoMove {
  NoCopyNoMove() : value(0) {}
  explicit NoCopyNoMove(int v) : value(v) {}
  NoCopyNoMove(const NoCopyNoMove&) = delete;
  NoCopyNoMove(NoCopyNoMove&&) = delete;

  NoCopyNoMove& operator=(const NoCopyNoMove&) = delete;
  NoCopyNoMove& operator=(NoCopyNoMove&&) = delete;
  int value;
};

struct FromNoCopy {
  explicit FromNoCopy(std::string_view v): value(v) { }
  explicit FromNoCopy(const NoCopy& nc): value(nc.value) { }
  std::string value;
  std::string get() { return value; }
};

struct CtorTakesPyObj {
  CtorTakesPyObj(PyObject *obj) {
    value = PyLong_AsLong(obj);
    if (value == -1 && PyErr_Occurred()) {
      PyErr_Clear();
    }
  }
  int value;
};

struct CtorTakesAbstract {
  CtorTakesAbstract(Abstract* obj): value(obj->value) { }
  int value;
};

struct CtorTakesAbstractVirtual {
  CtorTakesAbstractVirtual(Abstract* obj): value(obj->value) { }
  virtual int get() = 0;
  virtual ~CtorTakesAbstractVirtual() { }
  int value;
};

struct CtorTakesVector {
  CtorTakesVector(const std::vector<int>& vec): value(vec) { }
  std::vector<int> value;
};

struct ExtendedCtorTakesVector {
  std::vector<int> value;
};

struct CtorTakesSet {
  CtorTakesSet(const std::set<int>& s): value(s) { }
  std::set<int> value;
};

struct ExtendedCtorTakesSet {
  std::set<int> value;
};

struct CtorTakesUnorderedSet {
  CtorTakesUnorderedSet(const std::unordered_set<int>& s): value(s) { }
  std::unordered_set<int> value;
};

struct ExtendedCtorTakesUnorderedSet {
  std::unordered_set<int> value;
};

struct ExtendedCtorTakesPyObj {
  int value = -99999;
};

inline std::string abstract_reference_param(Abstract& obj) {
  return "abstract_reference";
}

inline std::string abstract_pointer_param(Abstract* obj) {
  return "abstract_pointer";
}

inline std::string nocopy_nomove_reference_param(const NoCopyNoMove&) {
  return "nocopy_nomove_reference";
}

inline std::string nocopy_nomove_pointer_param(NoCopyNoMove*) {
  return "nocopy_nomove_pointer";
}

inline std::string unique_pointer_param(std::unique_ptr<Abstract>) {
  return "unique_ptr";
}

struct Arg {
  int value;
};

struct TestCtor {
  int value;
  TestCtor(Arg arg = {10}): value(arg.value) { }
};

struct TestExtendCtor {
  int value;
};

struct NoDefaultConstructor {
  int value_;
  explicit NoDefaultConstructor(int v) : value_(v) {}
  int get() { return value_; }
};

inline NoDefaultConstructor no_default_ctor_return(
    int value, int* unused) {
  return NoDefaultConstructor(value);
}

inline std::unique_ptr<Derived> multiple_returns_with_unique_ptr(
    int* unused = nullptr) {
  return std::unique_ptr<Derived>(new Derived(10));
}

inline NoCopy multiple_returns_with_nocopy_object(int* unused = nullptr) {
  return NoCopy("20");
}

inline bool operator==(const Derived& lhs, const Derived& rhs) {
  return lhs.value == rhs.value;
}

inline std::string returns_one(int) {
  return "1";
}

inline int takes_vector(const std::vector<int>& vec) {
  return vec.size();
}

inline int takes_set(const std::set<int>& s) {
  return s.size();
}

inline int takes_unordered_set(const std::unordered_set<int>& s) {
  return s.size();
}

inline std::string takes_unique_ptr_vector(
    std::vector<std::unique_ptr<Derived>> vec) {
  return std::to_string(vec.size());
}

inline int consume_pyobject(const std::vector<PyObject*>& vec) {
  assert(PyGILState_Check());
  return vec.size();
}

struct TestCtxMgr {
  int value;
  void Enter() {
    this->value = 20;
  }
  void Close() { }
};

struct TestExtendCtxMgr {
  int value;
};

inline void python_exception_in_function() {
  PyErr_SetString(PyExc_ValueError, "Error in python_exception_in_function");
}

}  // namespace clif_testing

#endif  // THIRD_PARTY_CLIF_TESTING_LAMBDA_EXPRESSIONS_H_
