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
#ifndef CLIF_TESTING_STD_CONTAINERS_H_
#define CLIF_TESTING_STD_CONTAINERS_H_

#include <algorithm>
#include <array>
#include <functional>
#include <list>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

inline int PassVectorInt(const std::vector<int>& v) {
  int zum = 100;
  for (const int i : v) {
    zum += 2 * i;
  }
  return zum;
}

inline int PassListInt(const std::list<int>& l) {
  return PassVectorInt(std::vector<int>(l.begin(), l.end())) + 1;
}

inline int PassArrayInt2(const std::array<int, 2>& a) {
  return PassVectorInt(std::vector<int>(a.begin(), a.end())) + 2;
}

inline int PassVectorPairInt(const std::vector<std::pair<int, int>>& v) {
  int zum = 0;
  for (const auto& ij : v) {
    zum += ij.first * 100 + ij.second;
  }
  return zum;
}

inline int PassSetInt(const std::set<int>& s) {
  int zum = 200;
  for (const int i : s) {
    zum += 3 * i;
  }
  return zum;
}

inline int PassUnorderedSetInt(const std::unordered_set<int>& s) {
  int zum = 300;
  for (const int i : s) {
    zum += 4 * i;
  }
  return zum;
}

inline int PassMapInt(const std::map<int, int>& m) {
  int zum = 400;
  for (const auto& it : m) {
    zum += it.first * 100 + it.second;
  }
  return zum;
}

// list input arg and return value.
inline std::vector<int> Mul(std::vector<int> v, int m) {
  for (auto& i : v) { i *= m; }
  return v;
}

inline std::array<int, 2> Div(std::array<int, 2> v, int m) {
  return {v[0] / m, v[1] / m};
}

inline std::array<std::array<int, 2>, 3> Transpose(
    const std::array<std::array<int, 3>, 2>& m) {
  std::array<std::array<int, 2>, 3> tp;
  for (int i = 0; i < 2; i++) {
    for (int j = 0; j < 3; j++) {
      tp[j][i] = m[i][j];
    }
  }
  return tp;
}

inline std::vector<bool> Even(const std::vector<int>& v) {
  std::vector<bool> e(v.size());
  for (int i=0; i < v.size(); ++i) { if ((v[i] & 1) == 0) { e[i] = true; }}
  return e;
}

inline std::vector<bool>* Odd(const std::vector<int>& v) {
  static std::vector<bool> e;
  e.resize(v.size());
  std::fill(e.begin(), e.end(), false);
  for (int i=0; i < v.size(); ++i) { if (v[i] & 1) { e[i] = true; }}
  return &e;
}

// dict input arg.
inline bool Find(int val, std::unordered_map<int, int> m, int* key) {
  for (const auto& i : m)
    if (i.second == val) {
      if (key) *key = i.first;
      return true;
  }
  return false;
}

// list of lists return value.
inline std::vector<std::vector<int>> Ones(int r, int c) {
  std::vector<std::vector<int>> rows;
  for (int i = 0; i < r; ++i) {
    std::vector<int> columns(c, 1);
    rows.emplace_back(columns);
  }
  return rows;
}

// list of tuples return value
inline std::vector<std::pair<std::string, std::string>> Capitals() {
  std::vector<std::pair<std::string, std::string>> capitals;
  capitals.push_back(std::pair<std::string, std::string>("CA", "Sacramento"));
  capitals.push_back(std::pair<std::string, std::string>("OR", "Salem"));
  capitals.push_back(std::pair<std::string, std::string>("WA", "Olympia"));
  return capitals;
}

// list of lists input args and return value.
inline std::vector<std::vector<int>> MatrixSum(
    std::vector<std::vector<int>> a, std::vector<std::vector<int>> b) {
  std::vector<std::vector<int>> sum;
  for (size_t i = 0; i < a.size(); ++i) {
    sum.emplace_back(std::vector<int>(a[i].size()));
    for (size_t j = 0; j < a[i].size(); ++j) {
      sum[i][j] = a[i][j] + b[i][j];
    }
  }
  return sum;
}

inline std::string ConcatAllListListStr(
    const std::vector<std::vector<std::string>>& list_list_str) {
  std::string accu;
  for (const auto& list_str : list_list_str) {
    for (const auto& s : list_str) {
      accu += s;
      accu += ',';
    }
    accu += '$';
  }
  return accu;
}

inline std::tuple<std::tuple<int, int, int>, std::tuple<int, int, int>>
Make2By3() {
  return std::tuple<std::tuple<int, int, int>, std::tuple<int, int, int>>();
}

inline std::tuple<int, int, int, int, int, int> Flatten2By3(
const std::tuple<std::tuple<int, int, int>, std::tuple<int, int, int>>& m) {
  return std::make_tuple(std::get<0>(std::get<0>(m)),
                         std::get<1>(std::get<0>(m)),
                         std::get<2>(std::get<0>(m)),
                         std::get<0>(std::get<1>(m)),
                         std::get<1>(std::get<1>(m)),
                         std::get<2>(std::get<1>(m)));
}

inline void LastStringInVector(const std::vector<std::string>& v,
                               std::string* output) {
  if (!v.empty())
    *output = v.back();
  else
    output->clear();
}

inline const std::set<int>* GetConstPtrSetInt() {
  static const std::set<int>* singleton = new std::set<int>{50, 51, 52};
  return singleton;
}

inline std::unique_ptr<std::vector<int>> unique_ptr_vector_round_trip(
    std::unique_ptr<std::vector<int>> v = nullptr) {
  if (v) {
    return v;
  }
  return nullptr;
}

// Not supported by Leagcy PyCLIF
inline std::shared_ptr<std::vector<int>> return_shared_ptr_vector() {
  auto v = {1, 2, 3};
  auto result = std::make_shared<std::vector<int>>(v);
  return result;
}

// Not supported by Leagcy PyCLIF
inline int comsume_shared_ptr_vector(std::shared_ptr<std::vector<int>> v) {
  return v->size();
}

inline std::unique_ptr<std::unordered_map<int, int>>
    unique_ptr_unordered_map_round_trip(
        std::unique_ptr<std::unordered_map<int, int>> m = nullptr) {
  if (m) {
    return m;
  }
  return nullptr;
}

// Not supported by Leagcy PyCLIF
inline std::shared_ptr<std::unordered_map<int, int>>
    return_shared_ptr_unordered_map() {
  auto result = std::make_shared<std::unordered_map<int, int>>();
  result->insert({1, 2});
  result->insert({3, 4});
  result->insert({5, 6});
  return result;
}

// Not supported by Leagcy PyCLIF
inline int comsume_shared_ptr_unordered_map(
    std::shared_ptr<std::unordered_map<int, int>> v) {
  return v->size();
}

inline std::unique_ptr<std::unordered_set<int>>
    unique_ptr_unordered_set_round_trip(
        std::unique_ptr<std::unordered_set<int>> s = nullptr) {
  if (s) {
    return s;
  }
  return nullptr;
}

// Not supported by Leagcy PyCLIF
inline std::shared_ptr<std::unordered_set<int>>
    return_shared_ptr_unordered_set() {
  auto s = {1, 2, 3};
  auto result = std::make_shared<std::unordered_set<int>>(s);
  return result;
}

// Not supported by Leagcy PyCLIF
inline int consume_shared_ptr_unordered_set(
    std::shared_ptr<std::unordered_set<int>> v) {
  return v->size();
}

inline std::unique_ptr<std::pair<int, int>> unique_ptr_pair_round_trip(
    std::unique_ptr<std::pair<int, int>> p = nullptr) {
  if (p) {
    return p;
  }
  return nullptr;
}

// Not supported by Leagcy PyCLIF
inline std::shared_ptr<std::pair<int, int>> return_shared_ptr_pair() {
  auto result = std::make_shared<std::pair<int, int>>(
      std::pair<int, int>({1, 2}));
  return result;
}

// Not supported by Leagcy PyCLIF
inline int consume_shared_ptr_pair(std::shared_ptr<std::pair<int, int>> p) {
  return p->first;
}

struct IntHash {
  size_t operator()(const int source) const {
    return std::hash<int>{}(source);
  }
};

using MyUnorderedMap = std::unordered_map<int, int, IntHash>;
using MyUnorderedSet = std::unordered_set<int, IntHash>;

inline std::unique_ptr<MyUnorderedMap> create_unordered_map_customized_hash() {
  auto result = std::make_unique<MyUnorderedMap>();
  result->insert({1, 2});
  result->insert({3, 4});
  return result;
}

inline int consume_unordered_map_customized_hash(
    std::unique_ptr<MyUnorderedMap> ptr = nullptr) {
  if (!ptr) {
    return 0;
  }
  return ptr->size();
}

inline std::unique_ptr<MyUnorderedSet> create_unordered_set_customized_hash() {
  auto result = std::make_unique<MyUnorderedSet>();
  result->insert(1);
  result->insert(2);
  return result;
}

inline int consume_unordered_set_customized_hash(
    std::unique_ptr<MyUnorderedSet> ptr = nullptr) {
  if (!ptr) {
    return 0;
  }
  return ptr->size();
}

#endif  // CLIF_TESTING_STD_CONTAINERS_H_
