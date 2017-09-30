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
#ifndef CLIF_TESTING_SMART_PTRS_H_
#define CLIF_TESTING_SMART_PTRS_H_

#include <memory>

namespace smart_ptrs {

class A {
 public:
  int a_;
};

class B {
 public:
  B() : sp_(new A) { }
  explicit B(A* a) : sp_(a) { }

  std::shared_ptr<A> Get() {
    return sp_;
  }

  std::unique_ptr<A> GetNew() {
    std::unique_ptr<A> up(new A);
    *up = *sp_;
    return up;
  }

  void Set(A a) {
    A *p = new A;
    p->a_ = a.a_;
    sp_.reset(p);
  }

  void SetSP(std::shared_ptr<A> a) {
    sp_ = a;
  }

 private:
  std::shared_ptr<A> sp_;
};

inline B Func(std::unique_ptr<A> a) {
  return B(a.release());
}

class Operation {
 public:
  virtual ~Operation() { }
  virtual int Run() = 0;
};

inline int PerformUP(std::unique_ptr<Operation> op) {
  return op->Run();
}

inline int PerformSP(std::shared_ptr<Operation> op) {
  return op->Run();
}

// Class with protected destructor.
class C1 {
 public:
  int Get() {
    return a_;
  }

 protected:
  C1(int a) : a_(a) { }
  ~C1() { }

 private:
  int a_;
};

class D1 : public C1 {
 public:
  D1(int a) : C1(a) { }
  ~D1() { }
};

class WithPrivateDtor {
 public:
  static std::shared_ptr<WithPrivateDtor> New() {
    return {new WithPrivateDtor(), Destroy};
  }
  int Get() { return 321; }

 private:
  static void Destroy(WithPrivateDtor* p) { delete p; }
  ~WithPrivateDtor() = default;
};


class X { public: int y; };

std::unique_ptr<X> F3(std::unique_ptr<X> x) {
  return std::unique_ptr<X>(std::move(x));
}

}  // namespace smart_ptrs

#endif  // CLIF_TESTING_SMART_PTRS_H_
