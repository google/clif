#ifndef THIRD_PARTY_CLIF_TESTING_EXTEND_CLASSMETHODS_H_
#define THIRD_PARTY_CLIF_TESTING_EXTEND_CLASSMETHODS_H_

namespace clif_testing {

struct Abc {
  Abc(): value(0) {}
  Abc(int v): value(v) {}
  int get_value() { return value; }
  int value;

  static int static_value;
};

}  // namespace clif_testing

#endif  // THIRD_PARTY_CLIF_TESTING_EXTEND_CLASSMETHODS_H_
