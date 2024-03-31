#ifndef CLIF_TESTING_ABSL_CORD_H_
#define CLIF_TESTING_ABSL_CORD_H_

#include <string>
#include <string_view>

#include "absl/strings/cord.h"

namespace clif_testing_absl_cord {

inline std::string PassAbslCord(const absl::Cord& c) { return std::string(c); }
inline absl::Cord ReturnAbslCord(std::string_view v) { return absl::Cord(v); }

}  // namespace clif_testing_absl_cord

#endif  // CLIF_TESTING_ABSL_CORD_H_
