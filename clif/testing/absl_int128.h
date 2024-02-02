#ifndef CLIF_TESTING_ABSL_INT128_H_
#define CLIF_TESTING_ABSL_INT128_H_

#include <limits>

#include "absl/base/config.h"
#include "absl/numeric/int128.h"

namespace clif_test_absl_int128 {

inline absl::int128 Zero() { return 0; }
inline absl::int128 One() { return 1; }
inline absl::int128 NegativeOne() { return -1; }
inline absl::int128 SetHighLsb() { return absl::MakeInt128(1, 0); }
inline absl::int128 SetNegativeHighLsb() { return absl::MakeInt128(-1, 0); }
inline absl::int128 Min() { return std::numeric_limits<absl::int128>::min(); }
inline absl::int128 Max() { return std::numeric_limits<absl::int128>::max(); }
inline absl::int128 AddInt128(absl::int128 a, absl::int128 b) { return a + b; }

#ifdef ABSL_HAVE_INTRINSIC_INT128

inline constexpr bool kHasIntrinsicInt128 = true;

inline __int128 FromAbsl(absl::int128 value) { return __int128{value}; }
inline absl::int128 ToAbsl(__int128 value) { return absl::int128{value}; }

#else

inline constexpr bool kHasIntrinsicInt128 = false;

inline absl::int128 FromAbsl(absl::int128 /*value*/) { return 0; }
inline absl::int128 ToAbsl(absl::int128 /*value*/) { return 0; }

#endif

}  // namespace clif_test_absl_int128

#endif  // CLIF_TESTING_ABSL_INT128_H_
