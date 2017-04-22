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
#ifndef CLIF_TESTING_CALLBACK_H_
#define CLIF_TESTING_CALLBACK_H_

#include <functional>
#include <vector>

typedef std::function<int(const std::vector<int>&, std::vector<int>*)>
    OldCallback;
typedef std::function<std::pair<int, std::vector<int>>(const std::vector<int>&)>
    NewCallback;

std::vector<int> Function(const std::vector<int>& input, NewCallback callback) {
  auto output = callback(input);
  return output.second;
}

std::vector<int> Function(const std::vector<int>& input, OldCallback callback) {
  std::vector<int> output;
  callback(input, &output);
  return output;
}

struct SelfCallback {
  explicit SelfCallback(std::function<void(SelfCallback*)>) {}
};

#endif  // CLIF_TESTING_CALLBACK_H_
