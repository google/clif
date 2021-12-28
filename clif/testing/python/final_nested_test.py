from absl.testing import absltest

from clif.testing.python import final_nested


class FinalNestedTest(absltest.TestCase):

  def testInnerIsType(self):
    self.assertIsInstance(final_nested.Outer.Inner, type)


if __name__ == '__main__':
  absltest.main()
