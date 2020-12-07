#ifndef CLIF_TESTING_ABSL_INT128_H_
#define CLIF_TESTING_ABSL_INT128_H_

#include <cstdint>

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

}  // namespace clif_test_absl_int128

#endif  // CLIF_TESTING_ABSL_INT128_H_
