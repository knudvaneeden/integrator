import unittest

from parseintg import tokenize, parse
from elements import TrigFunction, Integral

class TestElements(unittest.TestCase):
  def test_tokenize(self):
    self.assertEqual(tokenize('a'), ['a'])
    self.assertEqual(tokenize('2'), ['2'])
    self.assertEqual(tokenize('2.3'), ['2.3'])

    self.assertEqual(tokenize('ab'), list('a*b'))
    self.assertEqual(tokenize('a*b'), list('a*b'))
    self.assertEqual(tokenize('a^b'), list('a^b'))
    self.assertEqual(tokenize('a/b'), list('a/b'))
    self.assertEqual(tokenize('a * b'), list('a*b'))
    self.assertEqual(tokenize('a ^ b'), list('a^b'))
    self.assertEqual(tokenize('a / b'), list('a/b'))
    self.assertEqual(tokenize('a * (b)'), list('a*(b)'))
    self.assertEqual(tokenize('a ^ (b)'), list('a^(b)'))
    self.assertEqual(tokenize('a / (b)'), list('a/(b)'))
    self.assertEqual(tokenize('a(b)'), list('a*(b)'))

    self.assertEqual(tokenize('a(b)d'), list('a*(b)*d'))
    self.assertEqual(tokenize('a(d)e'), list('a*(d)*e'))
    self.assertEqual(tokenize('ade'), ['a', 'de'])
    self.assertEqual(tokenize('ad e'), ['a', '*', 'd', '*', 'e'])

    self.assertEqual(tokenize('a(b(c)(d)e)f(g)2.3(4)'), list('a*(b*(c)*(d)*e)*f*(g)*') + ['2.3'] + list('*(4)'))

    self.assertEqual(tokenize('a+(b)+(ab)(c)'), list('a+(b)+(a*b)*(c)'))

    self.assertEqual(tokenize('int x dx'), ['int', 'x', 'dx'])
    self.assertEqual(tokenize('int dx'), ['int', 'dx'])

    self.assertEqual(tokenize('int (2) + 3x * 8 dx'), ['int', '(', '2', ')', '+', '3', '*', 'x', '*', '8', 'dx'])
    self.assertEqual(tokenize('int (2) + 3w * 8 dz'), ['int', '(', '2', ')', '+', '3', '*', 'w', '*', '8', 'dz'])

    self.assertEqual(tokenize('sin(x)'), ['sin', '(', 'x', ')'])
    self.assertEqual(tokenize('2cos(3*x+1)'), ['2', '*', 'cos', '(', '3', '*', 'x', '+', '1', ')'])

  def test_trig_parser(self):
    parsed = parse('int sin(3*x+2) dx')
    self.assertEqual(isinstance(parsed, Integral), True)
    self.assertEqual(isinstance(parsed.exp, TrigFunction), True)
    self.assertEqual(parsed.exp.name, 'sin')
    self.assertEqual(parse('asin(x)').name, 'asin')
    self.assertEqual(repr(parse('ln(x)')), 'ln(x)')
    self.assertEqual(repr(parse('log(x)')), 'log(x)')
    self.assertEqual(parse('arccos(x)').name, 'arccos')
    self.assertEqual(repr(parse('(1-x^2)^(-1/2)')),
      '((1 + (-1 * (x ^ 2))) ^ ((-1 * 1) / 2))')

  def test_named_constant_and_integral_leading_minus(self):
    self.assertEqual('epsilon' in repr(parse('int epsilon^2 dx')), True)
    self.assertEqual(r'\epsilon' in parse('int epsilon^2 dx').latex(), True)
    self.assertEqual(repr(parse('int -sin(x) dx')).startswith('int['), True)

  def test_parser(self):
    parsed = parse('int x^2 dx')
    self.assertEqual(isinstance(parsed, Integral), True)
    self.assertEqual(repr(parsed), 'int[(x ^ 2)]dx')


if __name__ == '__main__':
  unittest.main()
