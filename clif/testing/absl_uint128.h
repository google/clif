#ifndef CLIF_TESTING_ABSL_UINT128_H_
#define CLIF_TESTING_ABSL_UINT128_H_

#include <cstdint>

#include "absl/numeric/int128.h"

namespace clif_test_absl_uint128 {

inline constexpr std::uint64_t kMax64Bit = 0xFFFFFFFFFFFFFFFF;

inline absl::uint128 Zero() { return 0; }
inline absl::uint128 One() { return 1; }
inline absl::uint128 SetHighLsb() { return absl::MakeUint128(1, 0); }
inline absl::uint128 Max() { return absl::MakeUint128(kMax64Bit, kMax64Bit); }
inline absl::uint128 AddUint128(absl::uint128 a, absl::uint128 b) {
  return a + b;
}

}  // namespace clif_test_absl_uint128

#endif  // CLIF_TESTING_ABSL_UINT128_H_
