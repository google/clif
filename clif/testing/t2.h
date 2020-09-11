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
#ifndef CLIF_TESTING_T2_H_
#define CLIF_TESTING_T2_H_

#include <memory>
#include <vector>
#include <set>

// This comment intentionally includes UTF-8 characters as an IO test.
//   "Use pytype 🦆✔  - make code maintainers happy!"

class K {
 public:
  explicit K(int i): i_(i) {}
  static const int C = 1;
  int i1() const;
  int get2() const { return i_*i_; }
  int get() const { return i_; }
  void set(int i) { i_ = i; }
  static int getCplus2() { return C+2; }
 private:
  int i_;
};

bool takeK(const K&);
void k_modify(std::shared_ptr<K> k, int v);
std::unique_ptr<K> k_return();

class Derived : public K {
 public:
  int j;
  explicit Derived(int i = 0) : K(i), j(i) {}
  Derived(int i0, int j0) : K(i0), j(j0) {}
  bool has(int k);
};

class Abstract {
  Abstract() {}
 public:
  static constexpr char KIND[] = "pure virtual";
  virtual ~Abstract() {}
  virtual int Future() = 0;
};

class Inconstructible {
  Inconstructible() {}
 public:
  static int F() { return 0; }
};

class NoDefaultConstructor {
  int a_;
 public:
  explicit NoDefaultConstructor(int a) : a_(a) {}
  int A() { return a_; }
};

// Class 'NoCopy' is not CLIF copyable because it does not contain a copy
// constructor or a copy assignment operator.
class NoCopy {
  int a_;
  NoCopy(const NoCopy&) = delete;
  NoCopy& operator=(const NoCopy&) = delete;
 public:
  explicit NoCopy(int a = 0) : a_(a) {}
  int A() { return a_; }
};

// Class 'NoMove' is not CLIF movable because it does not contain a move
// constructor or a move assignment operator.
class NoMove {
  int a_;
  NoMove(const NoMove&) = default;
  NoMove& operator=(const NoMove&) = default;
  NoMove(NoMove&&) = delete;
  NoMove& operator=(NoMove&&) = delete;
 public:
  explicit NoMove(int a = 0) : a_(a) {}
  int A() { return a_; }
};

struct CtxMgr {
  CtxMgr(): state(CtxMgr::UNDEFINED) {}
  enum State { UNDEFINED, UNLOCKED, LOCKED };
  State state;
  void Lock() { state = CtxMgr::LOCKED; }
  void Unlock() { state = CtxMgr::UNLOCKED; }
};

struct Nested {
  struct Inner {
    int a;
  } i;
};

struct NestedContainerAttributes {
  std::vector<std::set<int>> int_set_vector;
};

std::vector<std::unique_ptr<NoCopy>> all_nocopy_holds();
std::unique_ptr<std::vector<Nested>> vector_inside_unique_ptr();

class MovableButUncopyable {
 public:
  explicit MovableButUncopyable(int a = 0) : a_(new int(a)) {}
  MovableButUncopyable(MovableButUncopyable&&) = default;
  MovableButUncopyable& operator=(MovableButUncopyable&&) = default;
  int get_a() { return *a_; }
  void set_a(int value) { a_.reset(new int(value)); }

 private:
  std::unique_ptr<int> a_;
};

MovableButUncopyable func_return_movable_but_uncopyable_type();

void take_nocopy_class(MovableButUncopyable*);

class OutputParameter {
 public:
  // The initial value of the output parameter "output" will not be reflected at
  // Python side. CLIF generated code constructs a "MovableButUncopyable" type
  // object and passes the address of the object into the function.
  //
  // The output parameter "output" can either modify the "MovableButUncopyable"
  // type object in CLIF generated code:
  void MovableButUncopyableOutputParameter1(MovableButUncopyable* output) {
    if (output) {
      output->set_a(100);
    }
  }

  // Or point to another "MovableButUncopyable" type object:
  void MovableButUncopyableOutputParameter2(MovableButUncopyable* output) {
    MovableButUncopyable temp(1);
    *output = std::move(temp);
  }
};

inline NoDefaultConstructor make_ndefctor(int x = 0) {
  return NoDefaultConstructor(x);
}
#endif  // CLIF_TESTING_T2_H_
