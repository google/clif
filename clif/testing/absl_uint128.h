#ifndef CLIF_TESTING_ABSL_UINT128_H_
#define CLIF_TESTING_ABSL_UINT128_H_

#include <cstdint>

#include "absl/base/config.h"
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

#ifdef ABSL_HAVE_INTRINSIC_INT128

inline constexpr bool kHasIntrinsicUint128 = true;

inline unsigned __int128 FromAbsl(absl::uint128 value) {
  return (unsigned __int128){value};
}
inline absl::uint128 ToAbsl(unsigned __int128 value) {
  return absl::uint128{value};
}

#else

inline constexpr bool kHasIntrinsicUint128 = false;

inline absl::uint128 FromAbsl(absl::uint128 /*value*/) { return 0; }
inline absl::uint128 ToAbsl(absl::uint128 /*value*/) { return 0; }

#endif

}  // namespace clif_test_absl_uint128

#endif  // CLIF_TESTING_ABSL_UINT128_H_
