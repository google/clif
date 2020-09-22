#ifndef THIRD_PARTY_CLIF_TESTING_PYTHON_EXTEND_DEFAULT_VALUE_CLIF_AUX_H_
#define THIRD_PARTY_CLIF_TESTING_PYTHON_EXTEND_DEFAULT_VALUE_CLIF_AUX_H_

#include "clif/testing/extend_default_value.h"

namespace clif_testing {

inline void Abc__extend__sum_and_set_values(
    Abc& self, int v1 = 10, int v2 = 100) {
  self.value = v1 + v2;
}

}  // namespace clif_testing

#endif  // THIRD_PARTY_CLIF_TESTING_PYTHON_EXTEND_DEFAULT_VALUE_CLIF_AUX_H_
