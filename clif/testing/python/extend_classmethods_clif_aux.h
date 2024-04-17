#ifndef CLIF_TESTING_PYTHON_EXTEND_CLASSMETHODS_CLIF_AUX_H_
#define CLIF_TESTING_PYTHON_EXTEND_CLASSMETHODS_CLIF_AUX_H_

#include "clif/testing/extend_classmethods.h"

namespace clif_testing {

inline Abc Abc__extend__from_value(int v) {
  return Abc(v);
}

inline int Abc__extend__get_static_value() {
  return Abc::static_value;
}

inline void Abc__extend__set_static_value(int v) {
  Abc::static_value = v;
}

inline int Abc__extend__function_with_defaults(int i = 3, int j = 5,
                                               int k = 7) {
  return (Abc::static_value * i + j) * k;
}

inline int TestNestedClassmethod_Inner__extend__get_static_value() {
  return 472;
}

}  // namespace clif_testing

#endif  // CLIF_TESTING_PYTHON_EXTEND_CLASSMETHODS_CLIF_AUX_H_
