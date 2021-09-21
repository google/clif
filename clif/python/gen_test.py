# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random
import unittest

from clif.python import gen


def BuildRandomIdepsForTopologicalSortSimple(n):
  # Build random DAG (Directed Acyclic Graph) by randomly ranking nodes and
  # adding dependencies only from lower to higher ranked nodes.
  ranks = list(range(n))
  random.shuffle(ranks)
  ideps = []
  for cons in range(n):
    prod = random.randrange(n)
    if prod == cons or ranks[prod] < ranks[cons]:
      prod = None
    ideps.append(prod)
  return ideps


def ValidateTopologicalSortPermutation(ideps, permutation):
  seen_before = set()
  for cons in permutation:
    prod = ideps[cons]
    if prod is not None and prod not in seen_before:
      return False
    seen_before.add(cons)
  return True


class GenTest(unittest.TestCase):

  def ValidateTopologicalSortPermutation(self, ideps, permutation):
    self.assertTrue(ValidateTopologicalSortPermutation(ideps, permutation))
    noop_permutation = list(range(len(ideps)))
    if permutation != noop_permutation:
      self.assertFalse(
          ValidateTopologicalSortPermutation(ideps, noop_permutation))

  def testTopologicalSortSimpleTabulatedTestCases(self):
    test_cases = (
        ([], []),
        ([None], [0]),
        ([None, None], [0, 1]),
        ([None, 0], [0, 1]),
        ([1, None], [1, 0]),
        ([1, 2, None], [2, 1, 0]),
        ([2, None, 1], [1, 2, 0]),
        ([1, 3, None, None], [3, 1, 0, 2]),
        ([2, 2, None], [2, 0, 1]),
        ([1, 3, 3, None], [3, 1, 0, 2]),
        ([3, 2, None, 1], [2, 1, 3, 0]),
    )
    for ideps, expected_permutation in test_cases:
      permutation = gen.TopologicalSortSimple(ideps)
      self.assertEqual(permutation, expected_permutation)
      self.ValidateTopologicalSortPermutation(ideps, permutation)

  def testTopologicalSortSimpleRandomTestCases(self):
    for n in range(2, 10):
      for unused_trial_counter in range(100):
        ideps = BuildRandomIdepsForTopologicalSortSimple(n)
        permutation = gen.TopologicalSortSimple(ideps)
        self.ValidateTopologicalSortPermutation(ideps, permutation)

  def testTopologicalSortSimpleExceptions(self):
    test_cases = (
        ([None, None, -3],
         'Negative value in ideps: ideps[2] = -3'),
        ([None, None, None, None, 7],
         'Value in ideps exceeds its length: ideps[4] = 7 >= 5'),
        ([None, None, None, 3],
         'Trivial cyclic dependency in ideps: ideps[3] = 3'),
        ([1, 0],
         'Cyclic dependency in ideps:' +
         ' following dependencies from 0 leads back to 0.'),
    )
    for ideps, expected_message in test_cases:
      with self.assertRaises(ValueError) as ctx:
        gen.TopologicalSortSimple(ideps)
      self.assertEqual(str(ctx.exception), expected_message)


if __name__ == '__main__':
  unittest.main()
