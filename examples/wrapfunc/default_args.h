/*
 * Copyright 2017 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#ifndef CLIF_EXAMPLES_WRAPFUNC_DEFAULT_ARGS_H_
#define CLIF_EXAMPLES_WRAPFUNC_DEFAULT_ARGS_H_

namespace clif_example {
namespace wrapfunc {

struct Ratios {
  int ratio1;
  int ratio2;
};

inline int Inc(int v, int d = 1) {
  return v + d;
}

inline int Scale(int v, int ratio = 2, int offset = 0) {
  return (v + offset) * ratio;
}

inline int ScaleWithRatios(int v, Ratios ratios = {1, 2}, int offset = 0) {
  if (v < 10) {
    return (v + offset) * ratios.ratio1;
  } else {
    return (v + offset) * ratios.ratio2;
  }
}

}  // namespace wrapfunc
}  // namespace clif_example

#endif  // CLIF_EXAMPLES_WRAPFUNC_DEFAULT_ARGS_H_
