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
#ifndef CLIF_TESTING_VIRTUAL_FUNCS_H_
#define CLIF_TESTING_VIRTUAL_FUNCS_H_

#include <Python.h>

#include <memory>
#include <vector>

struct B {
  int c;
  int get_c() { return c; }
  virtual void set_c(int i) { c = i; }
  virtual ~B() {}
  B() : c(0) {}
};

void Bset(B* b, int v) { b->set_c(v); }

struct D : B {
  void set_c(int i) override { c = (i > 0) ? i : -i; }
};

struct K {
  int i;
  K(): i(0) {}
  virtual ~K() {}
  virtual void inc(int) = 0;
};

std::vector<int> Kseq(K* k, int step, int stop) {
  std::vector<int> r;
  while (k->i <= stop) {
    r.push_back(k->i);
    k->inc(step);
  }
  return r;
}

struct Q {
  virtual ~Q() {}
  virtual bool PossiblyPush(int) = 0;
};

class AbstractClassNonDefConst {
 public:
  AbstractClassNonDefConst(int a, int b) : my_a(a), my_b(b) { }
  virtual ~AbstractClassNonDefConst()  { }

  virtual int DoSomething() const = 0;

  int my_a;
  int my_b;
 protected:
  virtual int get_a() { return my_a; }
};

inline int DoSomething(const AbstractClassNonDefConst& a) {
  return a.DoSomething();
}

class ClassNonDefConst {
 public:
  ClassNonDefConst(int a, int b) : my_a(a), my_b(b) { }
  virtual ~ClassNonDefConst() { }

  virtual int DoSomething() const { return my_a + my_b; }

  int my_a;
  int my_b;
};

class Manager {
 public:
  Manager(std::shared_ptr<ClassNonDefConst> c) : c_(c) {}
  int DoIt() { return c_->DoSomething(); }

 private:
  std::shared_ptr<ClassNonDefConst> c_;
};

inline int DoSomething(const ClassNonDefConst& a) {
  return a.DoSomething();
}

inline int add_seq(Q* q, int step, int stop) {
  int added = 0;
  for (int i=0; i <= stop; i+=step) {
    if (q->PossiblyPush(i)) ++added;
  }
  return added;
}

inline int DoUniq(std::unique_ptr<ClassNonDefConst> c) {
  return c->DoSomething();
}

struct TestReturnsObject {
  virtual PyObject* CreateObject() = 0;
  virtual ~TestReturnsObject() {}
  int GetRefcntOfResult() {
    PyObject* result = CreateObject();
    int refcnt = Py_REFCNT(result);
    Py_XDECREF(result);
    return refcnt;
  }
};

struct TestRenameVirtualFunctions {
  virtual int Func() const = 0;
  virtual ~TestRenameVirtualFunctions() {}
};

inline int CallFunc(const TestRenameVirtualFunctions& a) {
  return a.Func();
}

#endif  // CLIF_TESTING_VIRTUAL_FUNCS_H_
