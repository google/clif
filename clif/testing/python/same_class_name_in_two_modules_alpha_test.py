from absl.testing import absltest

from clif.testing.python import same_class_name_in_two_modules_alpha as alpha


class AlphaTest(absltest.TestCase):

  def testWhereIsHome(self):
    self.assertEqual(alpha.Smith.WhereIsHome(), 'I live in Alphaville.')


if __name__ == '__main__':
  absltest.main()
