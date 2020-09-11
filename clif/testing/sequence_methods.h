/*
 * Copyright 2020 Google LLC
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
#ifndef CLIF_TESTING_SEQUENCE_METHODS_H_
#define CLIF_TESTING_SEQUENCE_METHODS_H_

namespace clif_testing {

class TwoSequence {
 public:
  TwoSequence(int v0, int v1) : values{v0, v1} {}
  int length() const {
    for (int i = 2; i > 0; i--) {
      if (values[i - 1]) return i;
    }
    return 0;
  }
  TwoSequence concat(TwoSequence const& other) const {
    return TwoSequence(values[0], other.values[0]);
  }
  TwoSequence repeat(int count) const { return TwoSequence(values[0], count); }
  int item(int i) const { return values[i & 0x1]; }
  void ass_item(int i, int v) { values[i & 0x1] = v; }
  void ass_item(int i) { values[i & 0x1] = 0; }
  bool contains(int v) const { return values[0] == v || values[1] == v; }
  void inplace_concat(TwoSequence const& other) { values[1] = other.values[1]; }
  void inplace_repeat(int count) { values[1] = count; }

 private:
  int values[2];
};

}  // namespace clif_testing

#endif  // CLIF_TESTING_SEQUENCE_METHODS_H_
