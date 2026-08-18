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

  def test_log_one_plus_tangent_affine_rule(self):
    for problem in ['int log( 1 + tan( x ) ) dx',
      'int log( 1 + tan( 3*x+2 ) ) dx',
      'int ln( 1 + tan( 2*x-1 ) ) dx']:
      result = self.solve(problem)
      self.assertNotIn('int[', repr(result), problem)
      self.assertIn('Cl2(', repr(result), problem)
      self.assertIn(r'\operatorname{Cl}_2', result.latex(), problem)
    base_ten = self.solve('int log( 1 + tan( x ) ) dx')
    self.assertIn('ln(10)', repr(base_ten))

  def test_polynomial_times_exponential_requested_example(self):
    result = self.solve('int x^2 * exp( x ) dx')
    self.assertEqual(repr(result),
      '((exp(x) * (((x ^ 2) + (-2 * x)) + 2)) + C)')

  def test_square_root_over_affine_radicand(self):
    requested = self.solve('int sqrt( x ) / ( 1 + x ) dx')
    self.assertEqual(repr(requested),
      '(((2 * (x ^ (1 / 2))) + (-2 * arctan((x ^ (1 / 2))))) + C)')
    general = self.solve(
      'int sqrt( 2*x+1 ) / ( 3 + 5*(2*x+1) ) dx')
    self.assertNotIn('int[', repr(general))
    self.assertIn('arctan(', repr(general))

  def test_absolute_affine_logarithm(self):
    requested = self.solve('int sqrt( ln( x )^2 ) dx')
    self.assertIn('Piecewise', repr(requested))
    self.assertIn('x < 1', repr(requested))
    self.assertIn('x >= 1', repr(requested))
    self.assertIn('x*ln(x) - x + 2', repr(requested))
    general = self.solve('int sqrt( log( 3*x+2 )^2 ) dx')
    self.assertNotIn('int[', repr(general))
    self.assertIn('ln(10)', repr(general))

  def test_affine_power_uses_compact_substitution(self):
    requested = self.solve('int ( 2 * x + 3 )^5 dx')
    self.assertEqual(repr(requested),
      '(((((2 * x) + 3) ^ 6) / 12) + C)')
    general = self.solve('int ( 3 * x - 5 )^12 dx')
    self.assertNotIn('int[', repr(general))

  def test_fourth_power_times_exponential(self):
    result = self.solve('int x^4 * exp( x ) dx')
    self.assertEqual(repr(result),
      '((exp(x) * (((((x ^ 4) + (-4 * (x ^ 3))) + (12 * (x ^ 2))) '
      '+ (-24 * x)) + 24)) + C)')

  def test_sine_squared_with_affine_phase(self):
    result = self.solve('int sin( 2 * x )^2 dx')
    self.assertNotIn('int[', repr(result))
    self.assertIn('(x / 2)', repr(result))
    general = self.solve('int sin( 3 * x + 1 )^8 dx')
    self.assertNotIn('int[', repr(general))

  def test_general_logarithmic_derivative(self):
    requested = self.solve('int ( 2 * x^2 ) / ( 1 + x^3 ) dx')
    self.assertEqual(repr(requested), '(2*ln(x**3 + 1)/3 + C)')
    for problem in [
      'int ( 6*x + 2 ) / ( 3*x^2 + 2*x + 5 ) dx',
      'int cos( x ) / sin( x ) dx']:
      result = self.solve(problem)
      self.assertNotIn('int[', repr(result), problem)

  def test_general_rational_partial_fractions_quadratic(self):
    result = self.solve('int 1 / ( x^2 + x - 6 ) dx')
    self.assertEqual(repr(result),
      '(ln(x - 2)/5 - ln(x + 3)/5 + C)')

  def test_general_rational_repeated_irreducible_quadratic(self):
    result = self.solve('int 1 / ( x^2 + 1 )^2 dx')
    self.assertEqual(repr(result),
      '(x/(2*x**2 + 2) + atan(x)/2 + C)')

  def test_square_root_quadratic_over_x_uses_natural_log_notation(self):
    result = self.solve('int sqrt( 4 - x^2 ) / x dx')
    rendered = repr(result)
    self.assertNotIn('int[', rendered)
    self.assertIn('ln(', rendered)
    self.assertNotIn('log(', rendered)
    self.assertIn(r'\ln', result.latex())
    self.assertNotIn(r'\log', result.latex())

  def test_general_polynomial_quotient_with_irreducible_quadratic(self):
    result = self.solve('int x^2 / ( x^2 + 25 ) dx')
    self.assertEqual(repr(result), '(x - 5*atan(x/5) + C)')

  def test_quadratic_monomial_over_quadratic_square_root(self):
    result = self.solve('int x^2 / sqrt( x^2 + 25 ) dx')
    self.assertEqual(repr(result),
      '(x*sqrt(x**2 + 25)/2 - 25*asinh(x/5)/2 + C)')

  def test_strategy_applicability_rejects_nonmatching_radicals_cleanly(self):
    for problem in [
      'int sqrt( x^3 + x + 1 ) dx',
      'int sqrt( x^4 + 1 ) / ( x^2 + 1 ) dx']:
      result = self.solve(problem)
      self.assertIn('int[', repr(result), problem)

  def test_reciprocal_quadratic_square_root_numeric_and_parameter(self):
    numeric = self.solve('int 1 / sqrt( x^2 + 25 ) dx')
    parameter = self.solve('int 1 / sqrt( x^2 + a^2 ) dx')
    self.assertIn('ln(', repr(numeric))
    self.assertIn('ln(', repr(parameter))
    self.assertNotIn('int[', repr(numeric))
    self.assertNotIn('int[', repr(parameter))


if __name__ == '__main__':
  unittest.main()
