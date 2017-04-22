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
#ifndef CLIF_TESTING_T6_H_
#define CLIF_TESTING_T6_H_

#include <list>

typedef std::list<int> list_int;

inline list_int Repeat(const list_int& ls, unsigned int times) {
  list_int to;
  if (ls.size() && times)
    while (times--) std::copy(ls.begin(), ls.end(), std::back_inserter(to));
  return to;
}

#endif  // CLIF_TESTING_T6_H_
