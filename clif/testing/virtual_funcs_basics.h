#ifndef THIRD_PARTY_CLIF_TESTING_VIRTUAL_FUNCS_BASICS_H_
#define THIRD_PARTY_CLIF_TESTING_VIRTUAL_FUNCS_BASICS_H_

#include <vector>
#include <utility>

struct B {
  int c;
  int get_c() { return c; }
  virtual void set_c(int i) { c = i; }
  virtual std::pair<int, int> get_pair() { return {1, 2}; }
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

#endif  // THIRD_PARTY_CLIF_TESTING_VIRTUAL_FUNCS_BASICS_H_
