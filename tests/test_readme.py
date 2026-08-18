import unittest
from pathlib import Path

from parseintg import parse


class TestReadmeExamples(unittest.TestCase):
  CANONICAL_VERSION_72_COUNT = 311
  ADDED_VERSION_73 = ['int sqrt( x - sqrt( x^2 - 1 ) ) dx']
  ADDED_VERSION_74 = ['int sqrt( 2 * x - sqrt( 4 * x^2 - 1 ) ) dx']
  ADDED_VERSION_75 = ['int log( 1 + tan( x ) ) dx']
  ADDED_VERSION_76 = ['int x^2 * exp( x ) dx']
  ADDED_VERSION_77 = ['int sqrt( x ) / ( 1 + x ) dx']
  ADDED_VERSION_78 = ['int sqrt( ln( x )^2 ) dx']
  ADDED_VERSION_79 = ['int ( 2 * x + 3 )^5 dx']
  ADDED_VERSION_80 = ['int x^4 * exp( x ) dx']
  ADDED_VERSION_81 = ['int sin( 2 * x )^2 dx']
  ADDED_VERSION_82 = ['int ( 2 * x^2 ) / ( 1 + x^3 ) dx']
  ADDED_VERSION_83 = ['int 1 / ( x^2 + x - 6 ) dx']
  ADDED_VERSION_84 = ['int 1 / ( x^2 + 1 )^2 dx']
  ADDED_VERSION_85 = ['int sqrt( 4 - x^2 ) / x dx']
  ADDED_VERSION_58 = [
    'int sqrt( 5 * x + 4 ) dx',
    'int sin( x )^2 * cos( x ) dx',
    'int 4 - x^2 dx',
    'int 2 * x^2 - x^3 dx',
    'int 1 / x^2 - 1 / x^3 dx',
    'int 1 / x^(1/2) dx',
    'int 2 + x dx',
    'int 2 - x^2 dx',
    'int 3 - 2 * x + x^2 dx',
    'int x * ( 1 - x^2 ) dx',
    'int x * ( 1 - x ) * sqrt( x ) dx',
    'int sqrt( 1 + 3 * x ) dx',
    'int x^2 * ( x^3 + 1 ) dx',
    'int 1 / sqrt( 1 + x ) dx',
    'int x / sqrt( x^2 - 15 ) dx',
    'int x * ( 1 - sqrt( x ) )^2 dx']

  ADDED_VERSION_59 = [
    'int sqrt( x ) * exp( sqrt( x ) ) dx']

  ADDED_VERSION_60 = [
    'int 1 / ( 1 + x^3 ) dx']

  ADDED_VERSION_61 = [
    'int 1 / cos( sqrt( x ) ) dx']

  ADDED_VERSION_62 = [
    'int exp( x^2 ) dx']

  ADDED_VERSION_63 = [
    'int exp( x ) / x dx']

  ADDED_VERSION_64_COUNT = 71
  ADDED_VERSION_64_FIRST = 'int ( 1 + 2 * x^2 ) * exp( x^2 ) dx'
  ADDED_VERSION_64_LAST = 'int x / sqrt( 2 * E * x^2 + K * x - a^2 ) dx'

  ADDED_VERSION_66_COUNT = 132
  ADDED_VERSION_66_FIRST = 'int 2 * x^3 - 5 * x^2 + 3 * x + 1 dx'
  ADDED_VERSION_66_LAST = 'int ( x^2 + 3 ) / ( ( x - 1 )^3 * ( x + 1 ) ) dx'

  def _solved_examples(self):
    readme = Path(__file__).resolve().parents[1] / 'README.md'
    lines = readme.read_text().splitlines()
    start = lines.index('Solved:') + 1
    end = lines.index('===', start)
    return [line.strip() for line in lines[start:end] if line.strip()]

  def test_solved_examples_are_semantically_unique(self):
    examples = self._solved_examples()

    first_example_by_expression = {}
    duplicates = []
    for example in examples:
      expression = repr(parse(example).simplified())
      if expression in first_example_by_expression:
        duplicates.append((first_example_by_expression[expression], example))
      else:
        first_example_by_expression[expression] = example

    self.assertEqual(duplicates, [])

  def test_new_examples_are_the_final_readme_entries(self):
    examples = self._solved_examples()
    self.assertEqual(len(examples),
      self.CANONICAL_VERSION_72_COUNT + len(self.ADDED_VERSION_73)
      + len(self.ADDED_VERSION_74) + len(self.ADDED_VERSION_75)
      + len(self.ADDED_VERSION_76) + len(self.ADDED_VERSION_77)
      + len(self.ADDED_VERSION_78) + len(self.ADDED_VERSION_79)
      + len(self.ADDED_VERSION_80) + len(self.ADDED_VERSION_81)
      + len(self.ADDED_VERSION_82) + len(self.ADDED_VERSION_83)
      + len(self.ADDED_VERSION_84) + len(self.ADDED_VERSION_85))
    self.assertEqual(examples[0], 'int ( 1 + 2 * x^2 ) * exp( x^2 ) dx')
    added = (self.ADDED_VERSION_73 + self.ADDED_VERSION_74
      + self.ADDED_VERSION_75 + self.ADDED_VERSION_76)
    added += self.ADDED_VERSION_77
    added += self.ADDED_VERSION_78
    added += self.ADDED_VERSION_79
    added += self.ADDED_VERSION_80
    added += self.ADDED_VERSION_81
    added += self.ADDED_VERSION_82
    added += self.ADDED_VERSION_83
    added += self.ADDED_VERSION_84
    added += self.ADDED_VERSION_85
    self.assertEqual(examples[-len(added):], added)


if __name__ == '__main__':
  unittest.main()
