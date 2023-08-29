#ifndef CLIF_TESTING_PYTHON_EXTEND_DEFAULT_VALUE_CLIF_AUX_H_
#define CLIF_TESTING_PYTHON_EXTEND_DEFAULT_VALUE_CLIF_AUX_H_

#include <map>
#include <memory>

#include "clif/testing/extend_default_value.h"

namespace clif_testing {

inline void Abc__extend__sum_and_set_values(
    Abc& self, int v1 = 10, int v2 = 100) {
  self.value = v1 + v2;
}

inline int Abc__extend__pass_unique_ptr_kv_v(
    const Abc& self,
    std::unique_ptr<std::map<int, int>> kv = nullptr,
    int v = 8) {
  int retval = self.value + 46;
  if (kv) {
    for (auto i : *kv) {
      retval += i.first * 10 + i.second;
    }
  }
  return retval + v;
}

inline int Abc__extend__pass_unique_ptr_kv(
    const Abc& self,
    std::unique_ptr<std::map<int, int>> kv = nullptr) {
  return Abc__extend__pass_unique_ptr_kv_v(self, std::move(kv), 2);
}

inline int Abc__extend__pass_unique_ptr_v_kv(
    const Abc& self,
    int v = 4,
    std::unique_ptr<std::map<int, int>> kv = nullptr) {
  return Abc__extend__pass_unique_ptr_kv_v(self, std::move(kv), v);
}

inline int Abc__extend__pass_unique_ptr_v_kv_w(
    const Abc& self,
    int v = 5,
    std::unique_ptr<std::map<int, int>> kv = nullptr,
    int w = 9) {
  return Abc__extend__pass_unique_ptr_kv_v(self, std::move(kv), v * 100 + w);
}

inline std::unique_ptr<DefaultValueInConstructor>
DefaultValueInConstructor__extend__init__(
    int v = 10) {
  auto res = std::make_unique<DefaultValueInConstructor>();
  res->value = v;
  return res;
}

inline int TestNestedDefaultValue_Inner__extend__get_value(
    const TestNestedDefaultValue::Inner& self, int w = 800) {
  return self.value + w + 3;
}

}  // namespace clif_testing

#endif  // CLIF_TESTING_PYTHON_EXTEND_DEFAULT_VALUE_CLIF_AUX_H_
