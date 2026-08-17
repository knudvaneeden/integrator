import unittest

from elements import TrigFunction, VariableSet
from parseintg import parse
from solver import attempt_integral
from sublogger import SubLogger


class TestVersion72Restoration(unittest.TestCase):
  def solve(self, problem):
    return attempt_integral(parse(problem), SubLogger('test'))

  def test_post_version_66_general_rules(self):
    cases = [
      'int 1 / ( x^2 * sqrt( x^2 + 4 ) ) dx',
      'int 5 / ( x^2 * sqrt( 3 * x^2 + 7 ) ) dx',
      'int arctan( sqrt( x ) ) dx',
      'int arctan( sqrt( 3 * x + 2 ) ) dx',
      'int cos( x )^4 dx',
      'int sin( 3 * x + 2 )^6 dx',
      'int 1 / ( x * sqrt( x^2 - 1 ) ) dx',
      'int 3 / ( x * sqrt( 2 * x^2 - 5 ) ) dx']
    for problem in cases:
      self.assertNotIn('int[', repr(self.solve(problem)), problem)

  def test_cosine_fourth_power_is_elementary_and_flat(self):
    result = repr(self.solve('int cos( x )^4 dx'))
    self.assertIn('((sin(x) * (cos(x) ^ 3)) / 4)', result)
    self.assertIn('((3 * (sin(x) * cos(x))) / 8)', result)
    self.assertIn('((3 * x) / 8)', result)
    self.assertNotIn('beta', result.lower())

  def test_arcsec_mathjax_notation(self):
    x = VariableSet().variable('x')
    latex = TrigFunction('arcsec', x).latex()
    self.assertEqual(latex, r'\operatorname{arcsec}\left(x\right)')
    self.assertNotIn(r'\arcsec', latex)

  def test_nested_quadratic_radical_general_rule(self):
    cases = [
      'int sqrt( x - sqrt( x^2 - 1 ) ) dx',
      'int sqrt( 2*x+1 - sqrt( (2*x+1)^2 - 9 ) ) dx',
      'int sqrt( 2 * x - sqrt( 4 * x^2 - 1 ) ) dx',
      'int sqrt( 3*x+2 - sqrt( 9*x^2 + 12*x - 12 ) ) dx']
    for problem in cases:
      result = self.solve(problem)
      self.assertNotIn('int[', repr(result), problem)


if __name__ == '__main__':
  unittest.main()
