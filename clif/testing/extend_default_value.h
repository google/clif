#ifndef CLIF_TESTING_EXTEND_DEFAULT_VALUE_H_
#define CLIF_TESTING_EXTEND_DEFAULT_VALUE_H_

namespace clif_testing {

struct Abc {
  Abc(int v): value(v) {}
  int get_value() { return value; }
  int value;
};

struct DefaultValueInConstructor {
  DefaultValueInConstructor(): value(0) {}
  int value;
};

struct TestNestedDefaultValue {
  struct Inner {
    Inner(int v) : value{v + 70} {}
    int value;
  };
};

}  // namespace clif_testing

#endif  // CLIF_TESTING_EXTEND_DEFAULT_VALUE_H_
