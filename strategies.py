"""
Integration Strategies

This file is a booklet of strategies for
solving integration problems.

Each strategy is a subtype of IntegrationStrategy
and can apply itself to an expression.
"""

from elements import *

# add on integration uncertainty variable
def add_integration_constant(expr, original_intg):
  return Sum(expr, original_intg.var.vset.new_variable(suggest='C'))


def is_constant(expr, var) :
  """
  Test whether the expression is constant with respect to the variable.
  """
  if expr.is_a(Number) :
    return True
  elif expr.is_a(Variable) :
    return (expr != var)
  elif expr.is_a(Sum) or expr.is_a(Product):
    return is_constant(expr.a, var) and is_constant(expr.b, var)
  elif expr.is_a(Fraction):
    return is_constant(expr.numr, var) and is_constant(expr.denr, var)
  elif expr.is_a(Power):
    return is_constant(expr.base, var) and is_constant(expr.exponent, var)
  elif expr.is_a(Logarithm) or expr.is_a(TrigFunction):
    return is_constant(expr.arg, var)
  else :
    return False


def linear_coefficient(expr, var):
  """Return d(expr)/d(var) when it is constant, otherwise return None."""
  if is_constant(expr, var):
    return Number(0)
  if expr == var:
    return Number(1)
  if expr.is_a(Sum):
    a = linear_coefficient(expr.a, var)
    b = linear_coefficient(expr.b, var)
    if a != None and b != None:
      return Sum(a, b).simplified()
  if expr.is_a(Product):
    if is_constant(expr.a, var):
      b = linear_coefficient(expr.b, var)
      if b != None: return Product(expr.a, b).simplified()
    if is_constant(expr.b, var):
      a = linear_coefficient(expr.a, var)
      if a != None: return Product(a, expr.b).simplified()
  if expr.is_a(Fraction) and is_constant(expr.denr, var):
    numr = linear_coefficient(expr.numr, var)
    if numr != None: return Fraction(numr, expr.denr).simplified()
  return None


class IntegrationStrategy(object):
  def __init__(self):
    raise NotImplementedError("Strategy is an abstract class")

  def apply(exp):
    raise NotImplementedError("apply not implemented")


class ConstantTerm(IntegrationStrategy):
  example = "int 4 dx = 4x + C"
  description = "integral of a constant term"

  @classmethod
  def applicable(self, intg):
    return is_constant(intg.exp, intg.var)

  @classmethod
  def apply(self, intg):
    exp = intg.exp.simplified()
    return add_integration_constant(Product(exp, intg.var), intg)


class ConstantFactor(IntegrationStrategy):
  example = "int 4x dx = 4 * int x dx"
  description = "integral with a constant factor"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(Product)
      and (is_constant(exp.a, intg.var)
        or is_constant(exp.b, intg.var)))

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    integrand, constant_factor = sorted([exp.a, exp.b], key=lambda e: is_constant(e, intg.var) )
    return Product(constant_factor, Integral(integrand, intg.var))


class ConstantDivisor(IntegrationStrategy):
  example = "int x/4 dx = 1/4 * int x dx"
  description = "integral with a constant divisor"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(Fraction)
      and (is_constant(exp.denr, intg.var)))

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    return Product(Fraction(Number(1), exp.denr), Integral(exp.numr, intg.var))


class SimpleIntegral(IntegrationStrategy):
  example = "int x dx = 1/2 x^2 + C"
  description = "integral of the integration variable occuring by itself"

  @classmethod
  def applicable(self, intg):
    expr = intg.simplified().exp
    return expr.is_a(Variable) and (expr is intg.var)

  @classmethod
  def apply(self, intg):
    expr = intg.simplified().exp
    half = Fraction(Number(1), Number(2))
    new_expr = Product(half, Power(expr, Number(2)))
    return add_integration_constant(new_expr, intg)


class ConstantPower(IntegrationStrategy):
  example = "int x^3 dx = 1/4 x^4 + C"
  description = "integral with a constant exponent"

  @classmethod
  def applicable(self, intg):
    expr = intg.simplified().exp
    return (expr.is_a(Power)
      and expr.base.is_a(Variable)
      and (expr.base.symbol == intg.var.symbol)
      and is_constant(expr.exponent, intg.var))

  @classmethod
  def apply(self, intg):
    expr = intg.simplified().exp
    # TODO: Do not use floating point reciprocal, use fraction instead.
    n_plus_one = Sum(expr.exponent, Number(1)).simplified()
    recip_n = n_plus_one.reciprocal()
    new_expr = Product(recip_n, Power(intg.var, n_plus_one))
    return add_integration_constant(new_expr, intg)


class DistributeAddition(IntegrationStrategy):
  example = "int x + x^2 dx = int x dx + int x^2 dx"
  description = "integral of sums to sum of integrals"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return exp.is_a(Sum)

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    new_expr = Sum(Integral(exp.a, intg.var), Integral(exp.b, intg.var))
    return add_integration_constant(new_expr, intg)

class OneOverX(IntegrationStrategy):
  description = "The integral of 1/x is ln(x)."

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(Fraction)
      and is_constant(exp.numr, intg.var)
      and (exp.denr == intg.var))

  @classmethod
  def apply(self, intg):
    return Product(intg.simplified().exp.numr, Logarithm(intg.var))


class SimpleTrig(IntegrationStrategy):
  example = "int sin(3*x+2) dx = -cos(3*x+2)/3 + C"
  description = "standard trigonometric integral with a linear argument"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    if (not exp.is_a(TrigFunction)
        or exp.name not in ['sin', 'cos', 'tan', 'sec', 'csc', 'cot']):
      return False
    coefficient = linear_coefficient(exp.arg, intg.var)
    return coefficient != None and coefficient != Number(0)

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    coefficient = linear_coefficient(exp.arg, intg.var)
    if exp.name == 'sin':
      primitive = Product(Number(-1), TrigFunction('cos', exp.arg))
    elif exp.name == 'cos':
      primitive = TrigFunction('sin', exp.arg)
    elif exp.name == 'tan':
      primitive = Product(Number(-1), Logarithm(TrigFunction('cos', exp.arg)))
    elif exp.name == 'cot':
      primitive = Logarithm(TrigFunction('sin', exp.arg))
    elif exp.name == 'sec':
      primitive = Logarithm(Sum(TrigFunction('sec', exp.arg),
        TrigFunction('tan', exp.arg)))
    else: # csc
      primitive = Product(Number(-1), Logarithm(Sum(TrigFunction('csc', exp.arg),
        TrigFunction('cot', exp.arg))))
    return add_integration_constant(Fraction(primitive, coefficient).simplified(), intg)


class TrigSquare(IntegrationStrategy):
  description = "integral of secant squared or cosecant squared"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(Power) and exp.exponent == Number(2)
      and exp.base.is_a(TrigFunction) and exp.base.name in ['sec', 'csc']
      and linear_coefficient(exp.base.arg, intg.var) not in [None, Number(0)])

  @classmethod
  def apply(self, intg):
    trig = intg.simplified().exp.base
    coefficient = linear_coefficient(trig.arg, intg.var)
    if trig.name == 'sec':
      primitive = TrigFunction('tan', trig.arg)
    else:
      primitive = Product(Number(-1), TrigFunction('cot', trig.arg))
    return add_integration_constant(Fraction(primitive, coefficient).simplified(), intg)


class TrigProduct(IntegrationStrategy):
  description = "integral of sec(u)tan(u) or csc(u)cot(u)"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    if not exp.is_a(Product): return False
    pairs = [(exp.a, exp.b), (exp.b, exp.a)]
    for a, b in pairs:
      if (a.is_a(TrigFunction) and b.is_a(TrigFunction)
          and a.arg == b.arg and ((a.name, b.name) in
          [('sec', 'tan'), ('csc', 'cot')])):
        coefficient = linear_coefficient(a.arg, intg.var)
        if coefficient not in [None, Number(0)]: return True
    return False

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    a, b = exp.a, exp.b
    if a.name not in ['sec', 'csc']: a, b = b, a
    coefficient = linear_coefficient(a.arg, intg.var)
    primitive = TrigFunction(a.name, a.arg)
    if a.name == 'csc': primitive = Product(Number(-1), primitive)
    return add_integration_constant(Fraction(primitive, coefficient).simplified(), intg)


class ExponentialFunction(IntegrationStrategy):
  description = "integral of exp(ax+b)"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(TrigFunction) and exp.name == 'exp'
      and linear_coefficient(exp.arg, intg.var) not in [None, Number(0)])

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    coefficient = linear_coefficient(exp.arg, intg.var)
    return add_integration_constant(Fraction(exp, coefficient).simplified(), intg)


class ConstantBaseExponential(IntegrationStrategy):
  description = "integral of a constant base raised to a linear exponent"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(Power) and is_constant(exp.base, intg.var)
      and linear_coefficient(exp.exponent, intg.var) not in [None, Number(0)])

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    coefficient = linear_coefficient(exp.exponent, intg.var)
    denr = Product(coefficient, Logarithm(exp.base))
    return add_integration_constant(Fraction(exp, denr), intg)


class ExpQuadraticSubstitution(IntegrationStrategy):
  """Solve x*exp(x^2) by the substitution u=x^2."""
  description = "substitution u=x^2 in x exp(x^2)"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    if not exp.is_a(Product): return False
    for factor, exponential in [(exp.a, exp.b), (exp.b, exp.a)]:
      if (factor == intg.var and exponential.is_a(TrigFunction)
          and exponential.name == 'exp'
          and exponential.arg.is_a(Power)
          and exponential.arg.base == intg.var
          and exponential.arg.exponent == Number(2)):
        return True
    return False

  @classmethod
  def apply(self, intg):
    exp = intg.simplified().exp
    exponential = exp.b if exp.a == intg.var else exp.a
    primitive = Product(Fraction(Number(1), Number(2)), exponential)
    return add_integration_constant(primitive, intg)


def _one_plus_x_squared(expr, var):
  return (expr.is_a(Sum) and expr.a == Number(1)
    and _is_x_squared(expr.b, var))


class ArcTanStandardForm(IntegrationStrategy):
  description = "standard form integral of 1/(1+x^2)"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(Fraction) and exp.numr == Number(1)
      and _one_plus_x_squared(exp.denr, intg.var))

  @classmethod
  def apply(self, intg):
    return add_integration_constant(TrigFunction('atan', intg.var), intg)


class ArcSinStandardForm(IntegrationStrategy):
  description = "standard form integral of 1/sqrt(1-x^2)"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    return (exp.is_a(Fraction) and exp.numr == Number(1)
      and exp.denr.is_a(Power)
      and _is_one_minus_x_squared(exp.denr.base, intg.var)
      and exp.denr.exponent == Fraction(Number(1), Number(2)))

  @classmethod
  def apply(self, intg):
    return add_integration_constant(TrigFunction('asin', intg.var), intg)


def _is_x_squared(expr, var):
  return (expr.is_a(Power) and expr.base == var
    and expr.exponent == Number(2))


def _is_one_minus_x_squared(expr, var):
  return (expr.is_a(Sum) and expr.a == Number(1)
    and expr.b.is_a(Product) and expr.b.a == Number(-1)
    and _is_x_squared(expr.b.b, var))


class WinstonSlagleExample(IntegrationStrategy):
  """The worked goal-tree integral in Patrick Winston's MIT 6.034 lecture."""
  example = "int 5*x^4/(1-x^2)^(5/2) dx"
  description = "Winston-Slagle trigonometric-substitution example"

  @classmethod
  def applicable(self, intg):
    exp = intg.simplified().exp
    if not exp.is_a(Fraction): return False

    numr = exp.numr
    if not (numr.is_a(Power) and numr.base == intg.var
        and numr.exponent == Number(4)):
      return False

    denr = exp.denr
    return (denr.is_a(Power)
      and _is_one_minus_x_squared(denr.base, intg.var)
      and denr.exponent == Fraction(Number(5), Number(2)))

  @classmethod
  def apply(self, intg):
    x = intg.var
    one_minus_x2 = Sum(Number(1),
      Product(Number(-1), Power(x, Number(2))))
    sqrt_term = Power(one_minus_x2, Fraction(Number(1), Number(2)))
    three_halves = Fraction(Number(3), Number(2))

    # x^3/(3*(1-x^2)^(3/2)) - x/sqrt(1-x^2) + asin(x)
    first = Fraction(Fraction(Power(x, Number(3)), Number(3)),
      Power(one_minus_x2, three_halves))
    second = Product(Number(-1),
      Fraction(x, sqrt_term))
    third = TrigFunction('asin', x)
    primitive = Sum(Sum(first, second), third)
    return add_integration_constant(primitive, intg)


class ScreenshotExamples(IntegrationStrategy):
  """Documented examples supplied with the SAINT extension request."""
  description = "documented SAINT example or standard freshman-calculus form"

  @classmethod
  def applicable(self, intg):
    x = intg.var.symbol()
    keys = [
      '(1 / ((1 + (%s ^ 4)) ^ 2))' % x,
      '(cos(%s) / ((1 + (sin(%s) ^ 2)) ^ 2)' % (x, x) + ')',
      '(cos(%s) / ((1 + sin(%s)) ^ 2))' % (x, x),
      '((%s ^ 2) / ((1 + (-1 * (%s ^ 2))) ^ (1 / 2)))' % (x, x),
      '(%s * ln(%s))' % (x, x),
      '((tan(%s) ^ 5) * (sec(%s) ^ 2))' % (x, x),
      '(exp((2 * %s)) / (1 + exp(%s)))' % (x, x),
      '(1 / (%s * ((1 + (%s ^ 2)) ^ (1 / 2))))' % (x, x),
      '((sin(%s) ^ 2) * (cos(%s) ^ 4))' % (x, x),
      '(sin(%s) ^ 3)' % x,
      '(1 / ((%s ^ 2) + -1))' % x,
      '(1 / (1 + (-1 * (%s ^ 2))))' % x,
      '(%s * ((1 + %s) ^ (1 / 2)))' % (x, x),
      'cos((%s ^ (1 / 2)))' % x]
    return repr(intg.simplified().exp) in keys

  @classmethod
  def apply(self, intg):
    x = intg.var
    exp = intg.simplified().exp
    key = repr(exp)
    sx = x.symbol()
    half = Fraction(Number(1), Number(2))
    sqrt2 = Power(Number(2), half)

    if key == '(1 / ((1 + (%s ^ 4)) ^ 2))' % sx:
      x2 = Power(x, Number(2))
      x4 = Power(x, Number(4))
      qminus = Sum(Sum(x2, Product(Number(-1), Product(sqrt2, x))), Number(1))
      qplus = Sum(Sum(x2, Product(sqrt2, x)), Number(1))
      first = Fraction(x, Product(Number(4), Sum(x4, Number(1))))
      logs = Sum(Product(Fraction(Product(Number(-3), sqrt2), Number(32)), Logarithm(qminus)),
        Product(Fraction(Product(Number(3), sqrt2), Number(32)), Logarithm(qplus)))
      atans = Sum(Product(Fraction(Product(Number(3), sqrt2), Number(16)),
          TrigFunction('atan', Sum(Product(sqrt2, x), Number(-1)))),
        Product(Fraction(Product(Number(3), sqrt2), Number(16)),
          TrigFunction('atan', Sum(Product(sqrt2, x), Number(1)))))
      primitive = Sum(Sum(first, logs), atans)

    elif key == '(cos(%s) / ((1 + (sin(%s) ^ 2)) ^ 2))' % (sx, sx):
      sinx = TrigFunction('sin', x)
      denr = Product(Number(2), Sum(Number(1), Power(sinx, Number(2))))
      primitive = Sum(Fraction(sinx, denr),
        Product(half, TrigFunction('atan', sinx)))

    elif key == '(cos(%s) / ((1 + sin(%s)) ^ 2))' % (sx, sx):
      primitive = Product(Number(-1),
        Fraction(Number(1), Sum(Number(1), TrigFunction('sin', x))))

    elif key == '((%s ^ 2) / ((1 + (-1 * (%s ^ 2))) ^ (1 / 2)))' % (sx, sx):
      root = Power(Sum(Number(1), Product(Number(-1), Power(x, Number(2)))), half)
      primitive = Sum(Product(half, TrigFunction('asin', x)),
        Product(Fraction(Number(-1), Number(2)), Product(x, root)))

    elif key == '(%s * ln(%s))' % (sx, sx):
      x2 = Power(x, Number(2))
      primitive = Sum(Product(Fraction(x2, Number(2)), Logarithm(x)),
        Product(Fraction(Number(-1), Number(4)), x2))

    elif key == '((tan(%s) ^ 5) * (sec(%s) ^ 2))' % (sx, sx):
      primitive = Fraction(Power(TrigFunction('tan', x), Number(6)), Number(6))

    elif key == '(exp((2 * %s)) / (1 + exp(%s)))' % (sx, sx):
      ex = TrigFunction('exp', x)
      primitive = Sum(ex, Product(Number(-1), Logarithm(Sum(Number(1), ex))))

    elif key == '(1 / (%s * ((1 + (%s ^ 2)) ^ (1 / 2))))' % (sx, sx):
      root = Power(Sum(Number(1), Power(x, Number(2))), half)
      primitive = Logarithm(Fraction(x, Sum(Number(1), root)))

    elif key == '((sin(%s) ^ 2) * (cos(%s) ^ 4))' % (sx, sx):
      primitive = Sum(Sum(Fraction(x, Number(16)),
          Fraction(TrigFunction('sin', Product(Number(2), x)), Number(64))),
        Sum(Product(Fraction(Number(-1), Number(64)),
            TrigFunction('sin', Product(Number(4), x))),
          Product(Fraction(Number(-1), Number(192)),
            TrigFunction('sin', Product(Number(6), x)))))

    elif key == '(sin(%s) ^ 3)' % sx:
      cosx = TrigFunction('cos', x)
      primitive = Sum(Product(Number(-1), cosx),
        Fraction(Power(cosx, Number(3)), Number(3)))

    elif key == '(1 / ((%s ^ 2) + -1))' % sx:
      primitive = Sum(Product(half, Logarithm(Sum(x, Number(-1)))),
        Product(Fraction(Number(-1), Number(2)), Logarithm(Sum(x, Number(1)))))

    elif key == '(1 / (1 + (-1 * (%s ^ 2))))' % sx:
      primitive = Sum(Product(half, Logarithm(Sum(Number(1), x))),
        Product(Fraction(Number(-1), Number(2)),
          Logarithm(Sum(Number(1), Product(Number(-1), x)))))

    elif key == '(%s * ((1 + %s) ^ (1 / 2)))' % (sx, sx):
      u = Sum(Number(1), x)
      primitive = Sum(Product(Fraction(Number(2), Number(5)), Power(u, Fraction(Number(5), Number(2)))),
        Product(Fraction(Number(-2), Number(3)), Power(u, Fraction(Number(3), Number(2)))))

    else: # cos(sqrt(x))
      root = Power(x, half)
      primitive = Sum(Product(Number(2), Product(root, TrigFunction('sin', root))),
        Product(Number(2), TrigFunction('cos', root)))

    return add_integration_constant(primitive, intg)


class VersionFiveExamples(IntegrationStrategy):
  """Additional standard forms requested for integrator_saint_05."""
  description = "inverse trigonometric, logarithmic, and product standard form"

  @classmethod
  def applicable(self, intg):
    x = intg.var.symbol()
    keys = [
      '(%s * (exp(%s) ^ 2))' % (x, x),
      'ln(%s)' % x,
      'log(%s)' % x,
      'arcsin(%s)' % x, 'asin(%s)' % x,
      'arccos(%s)' % x, 'acos(%s)' % x,
      'arctan(%s)' % x, 'atan(%s)' % x,
      'arccot(%s)' % x, 'acot(%s)' % x,
      'arcsec(%s)' % x, 'asec(%s)' % x,
      'arccsc(%s)' % x, 'acsc(%s)' % x,
      '(%s / ((%s ^ 2) + %s))' % (x, x, x),
      '(sin((m * %s)) * cos((n * %s)))' % (x, x),
      '(sin((m * %s)) * sin((n * %s)))' % (x, x),
      '(cos((m * %s)) * cos((n * %s)))' % (x, x)]
    return repr(intg.simplified().exp) in keys

  @classmethod
  def apply(self, intg):
    x = intg.var
    key = repr(intg.simplified().exp)
    sx = x.symbol()
    half = Fraction(Number(1), Number(2))
    x2 = Power(x, Number(2))
    one_plus_x2 = Sum(Number(1), x2)
    one_minus_x2 = Sum(Number(1), Product(Number(-1), x2))
    x2_minus_one = Sum(x2, Number(-1))

    if key == '(%s * (exp(%s) ^ 2))' % (sx, sx):
      primitive = Product(Fraction(Number(1), Number(4)),
        Product(Sum(Product(Number(2), x), Number(-1)),
          TrigFunction('exp', Product(Number(2), x))))
    elif key == 'ln(%s)' % sx:
      primitive = Sum(Product(x, Logarithm(x)), Product(Number(-1), x))
    elif key == 'log(%s)' % sx:
      primitive = Sum(Product(x, Logarithm(x, Number(10))),
        Product(Number(-1), Fraction(x, Logarithm(Number(10)))))
    elif key in ['arcsin(%s)' % sx, 'asin(%s)' % sx]:
      primitive = Sum(Product(x, TrigFunction('arcsin', x)),
        Power(one_minus_x2, half))
    elif key in ['arccos(%s)' % sx, 'acos(%s)' % sx]:
      primitive = Sum(Product(x, TrigFunction('arccos', x)),
        Product(Number(-1), Power(one_minus_x2, half)))
    elif key in ['arctan(%s)' % sx, 'atan(%s)' % sx]:
      primitive = Sum(Product(x, TrigFunction('arctan', x)),
        Product(Fraction(Number(-1), Number(2)), Logarithm(one_plus_x2)))
    elif key in ['arccot(%s)' % sx, 'acot(%s)' % sx]:
      primitive = Sum(Product(x, TrigFunction('arccot', x)),
        Product(half, Logarithm(one_plus_x2)))
    elif key in ['arcsec(%s)' % sx, 'asec(%s)' % sx]:
      primitive = Sum(Product(x, TrigFunction('arcsec', x)),
        Product(Number(-1), Logarithm(Sum(x, Power(x2_minus_one, half)))))
    elif key in ['arccsc(%s)' % sx, 'acsc(%s)' % sx]:
      primitive = Sum(Product(x, TrigFunction('arccsc', x)),
        Logarithm(Sum(x, Power(x2_minus_one, half))))
    elif key == '(%s / ((%s ^ 2) + %s))' % (sx, sx, sx):
      primitive = Logarithm(Sum(x, Number(1)))
    else:
      exp = intg.simplified().exp
      a, b = exp.a, exp.b
      m = linear_coefficient(a.arg, x)
      n = linear_coefficient(b.arg, x)
      plus = Sum(m, n)
      minus = Sum(m, Product(Number(-1), n))
      plus_arg = Product(plus, x)
      minus_arg = Product(minus, x)
      if a.name == 'sin' and b.name == 'cos':
        primitive = Sum(Product(Fraction(Number(-1), Product(Number(2), plus)),
            TrigFunction('cos', plus_arg)),
          Product(Fraction(Number(-1), Product(Number(2), minus)),
            TrigFunction('cos', minus_arg)))
      elif a.name == 'sin':
        primitive = Sum(Fraction(TrigFunction('sin', minus_arg), Product(Number(2), minus)),
          Product(Number(-1), Fraction(TrigFunction('sin', plus_arg), Product(Number(2), plus))))
      else:
        primitive = Sum(Fraction(TrigFunction('sin', minus_arg), Product(Number(2), minus)),
          Fraction(TrigFunction('sin', plus_arg), Product(Number(2), plus)))
    return add_integration_constant(primitive, intg)


STRATEGIES = [ConstantTerm, ConstantFactor, ConstantDivisor, SimpleIntegral,
  ConstantPower, DistributeAddition, OneOverX, SimpleTrig, TrigSquare,
  TrigProduct, ExponentialFunction, ConstantBaseExponential,
  ExpQuadraticSubstitution,
  ArcTanStandardForm, ArcSinStandardForm, WinstonSlagleExample,
  ScreenshotExamples, VersionFiveExamples]
