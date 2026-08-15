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
    raise "Strategy is an abstract class"

  def apply(exp):
    raise "apply not implemented"


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
    if not (numr.is_a(Product) and numr.a == Number(5)
        and numr.b.is_a(Power) and numr.b.base == intg.var
        and numr.b.exponent == Number(4)):
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

    # 5/3*x^3/(1-x^2)^(3/2) - 5*x/sqrt(1-x^2) + 5*asin(x)
    first = Fraction(Product(Fraction(Number(5), Number(3)),
      Power(x, Number(3))), Power(one_minus_x2, three_halves))
    second = Product(Number(-1),
      Fraction(Product(Number(5), x), sqrt_term))
    third = Product(Number(5), TrigFunction('asin', x))
    primitive = Sum(Sum(first, second), third)
    return add_integration_constant(primitive, intg)


STRATEGIES = [ConstantTerm, ConstantFactor, ConstantDivisor, SimpleIntegral,
  ConstantPower, DistributeAddition, OneOverX, SimpleTrig, TrigSquare,
  TrigProduct, WinstonSlagleExample]
