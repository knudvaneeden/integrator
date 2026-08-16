# Integration-rule audit

This audit was completed for version 1.0.0.0.48 and extended in version
1.0.0.0.49. A rule is considered ad hoc
when its applicability test recognizes only one fixed expression rather than a
mathematical family with parameters.

## Replaced or retired

The following fixed-expression rules were removed and their examples now pass
through general strategies:

- `ExpQuadraticSubstitution` was replaced by
  `PolynomialDerivativeExponentialSubstitution`, which integrates
  `c*Q'(x)*exp(Q(x))` for rational-coefficient polynomials `Q`.
- `CosOverOneMinusSinSquared` and `SineSquaredTimesCosine` were replaced by
  `TrigBinomialPowerSubstitution`, which integrates derivative factors times
  arbitrary rational powers of affine binomials in sine or cosine.
- `LinearOverQuadraticRoot` and `ShiftedCircleRoot` were replaced by
  `LinearOverQuadraticSquareRoot`, which handles a general rational linear
  numerator over the square root of a rational quadratic.
- `ExponentialQuotientDerivative` was replaced by
  `ExponentialOverLinearQuotientDerivative`, a parameterized reverse-quotient
  rule for exponentials over linear functions.
- `ExponentialLogSubstitution` was replaced by
  `ExponentialBinomialLogSubstitution`, covering scaled and shifted
  exponential binomials.
- `VariableTimesLinearBinomial` was retired; its example is handled by
  `PolynomialTimesAffinePowerSubstitution`.
- `SineFourthOverCosineFourth` and `ReciprocalCotangentFourth` were replaced by
  `TangentIntegerPowerReduction`, covering every nonnegative integer tangent
  power with an affine argument.
- `ArcTanStandardForm` was retired; it is contained in
  `LaurentPolynomialOverOnePlusSquare`.
- Duplicate legacy branches for `tan(x)^5*sec(x)^2`, `x*sqrt(1+x)`,
  `cos(sqrt(x))`, and `cos(x)/(1+sin(x))^2` were removed because general rules
  now handle them before the legacy example registry.

## General strategies retained

The foundational linearity, constant, power, affine trigonometric,
exponential, polynomial, Laurent-polynomial, quadratic-substitution,
trigonometric-binomial, tangent-power, and exponential-binomial strategies are
parameterized families and are not ad hoc.

## Specialized rules retained

The following rules still recognize restricted forms. They were retained
because replacing them correctly requires a substantially broader subsystem,
not merely a parameterized version of the same substitution:

- `SecSquaredRationalTangent`: requires general rational-function integration
  after substituting `tan(x)`.
- `CompositeSquareSubstitution`: requires a canonical symbolic derivative
  matcher for arbitrary composite expressions.
- `SquaredFractionalPowerBinomial`: requires general algebraic expansion and
  normalization of fractional powers.
- `ExponentialRationalSubstitution`: requires rational integration after a
  common exponential substitution.
- `SineFourthCosineFourth` and the remaining trigonometric-power examples:
  require a general integer sine/cosine power-reduction engine.
- `RationalEvenFourthProduct`, `WinstonSlagleExample`, and the remaining
  rational examples: require polynomial factorization, Hermite reduction, and
  general partial fractions.
- The remaining inverse-trigonometric and logarithmic entries in
  `VersionFiveExamples`: require general integration-by-parts templates plus
  canonical derivative simplification.
- The remaining entries in `ScreenshotExamples` are documented benchmark
  forms pending those algebraic and rational-integration subsystems.

These retained rules remain covered by regression tests. No working solved
example was removed during the consolidation.

## Version 1.0.0.0.49 follow-up

The requested example-by-example review added further general families:

- Integer powers of binomials in `sin(u)^2` or `cos(u)^2`, using binomial
  expansion and even-power reduction.
- Both `1/(1+cos(u))` and `1/(1-cos(u))` with affine `u` in one half-angle
  strategy.
- `c*exp(u)/(d+e*exp(2u))`, including arctangent and logarithmic sign cases.
- Products of an affine exponential with an affine sine or cosine.
- Every nonnegative integer secant power by reduction, and arbitrary symbolic
  constant secant powers through the Gauss hypergeometric function.
- `1/sqrt(x^2+B*x+C)` with symbolic parameters constant in `x`.
