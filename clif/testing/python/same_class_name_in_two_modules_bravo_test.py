from absl.testing import absltest

from clif.testing.python import same_class_name_in_two_modules_bravo as bravo


class BravoTest(absltest.TestCase):

  def testWhereIsHome(self):
    self.assertEqual(bravo.Smith.WhereIsHome(), 'I live in Bravoville.')


if __name__ == '__main__':
  absltest.main()
