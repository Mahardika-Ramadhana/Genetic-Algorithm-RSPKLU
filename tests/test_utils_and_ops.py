import unittest
import random
import sys
import os

# ensure project root is on sys.path for imports when running tests directly
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils import split_routes, join_routes
from ga.operators import selection
import mutation


class TestUtilsAndOperators(unittest.TestCase):
    def test_split_join_roundtrip(self):
        chrom = ['D1', 'C1', 'C2', 'D1', '|', 'D2', 'C3', 'D2']
        routes = split_routes(chrom)
        self.assertEqual(join_routes(routes), chrom)

    def test_selection_basic(self):
        pop = [['a'], ['b'], ['c']]
        fitness = [10.0, 5.0, 7.0]
        parents = selection(pop, fitness, elite_size=1, tournament_size=2)
        # elites preserved
        self.assertIn(['b'], parents)
        self.assertEqual(len(parents), len(pop))

    def test_reassign_customer_to_depot(self):
        chrom = ['D1', 'C1', 'D1', '|', 'D2', 'C2', 'D2']
        # move C1 from D1 to D2
        new = mutation.reassign_customer_to_depot(chrom, 'C1', 'D1', 'D2')
        self.assertIn('C1', new)
        # ensure delimiter encoding preserved
        self.assertIsInstance(new, list)


if __name__ == '__main__':
    random.seed(1)
    unittest.main()
