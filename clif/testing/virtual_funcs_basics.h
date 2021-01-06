#ifndef THIRD_PARTY_CLIF_TESTING_VIRTUAL_FUNCS_BASICS_H_
#define THIRD_PARTY_CLIF_TESTING_VIRTUAL_FUNCS_BASICS_H_

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

#endif  // THIRD_PARTY_CLIF_TESTING_VIRTUAL_FUNCS_BASICS_H_
