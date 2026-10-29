"""Consumer-visible support and structural invariants for production generation."""

import contextlib
import io
import math
import random
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import qr_filter as generator


class AscendingEntropy(random.Random):
    """Drive Random.sample's real selection algorithm toward the edge 1..10."""

    def __init__(self):
        super().__init__(0)
        self.position = 0

    def _randbelow(self, n):
        if n == 12:  # Independent special draw: choose 1, including overlaps.
            return 0
        position = self.position
        self.position += 1
        return position


class UniformGenerationTests(unittest.TestCase):
    def test_full_support_edge_is_not_rejected(self):
        outside = (1, 2, 3, 4, 5)
        self.assertGreater(generator.distance_squared(outside), generator.QR80_THRESHOLD)
        with patch.object(generator, '_RNG', AscendingEntropy()):
            self.assertEqual(generator.sample_uniform_ticket(), outside)
        with patch.object(generator, '_RNG', AscendingEntropy()):
            result = generator.suggest_uniform(1)[0]
        self.assertEqual(tuple(result['combo']), outside)
        self.assertFalse(result['in_qr80'])
        self.assertEqual(result['special_info']['special'], 1)
        self.assertTrue(result['special_info']['is_overlap'])

    def test_batch_is_without_replacement_but_specials_are_free(self):
        with patch.object(generator, '_RNG', random.Random(17)):
            rows = generator.suggest_uniform(60)
        mains = [tuple(row['combo']) for row in rows]
        self.assertEqual(len(set(mains)), len(mains))
        self.assertTrue(all(len(main) == 5 and len(set(main)) == 5 and
                            all(1 <= number <= 35 for number in main) for main in mains))
        self.assertTrue(all(1 <= row['special_info']['special'] <= 12 for row in rows))
        self.assertIn(False, [row['in_qr80'] for row in rows])
        self.assertIn(True, [row['in_qr80'] for row in rows])

    def test_history_descriptors_do_not_change_selected_tickets(self):
        latest = dict(draw_code='previous', num1=1, num2=2, num3=3, num4=4, num5=5)
        first_context = (None, {number: 0 for number in range(1, 36)})
        second_context = (latest, {number: 100 for number in range(1, 36)})
        selections = []
        for context in (first_context, second_context):
            with patch.object(generator, '_RNG', random.Random(321)), \
                 patch.object(generator, 'get_history_context', return_value=context):
                rows = generator.suggest_uniform(12)
            selections.append([(tuple(row['combo']), row['special_info']['special']) for row in rows])
        self.assertEqual(*selections)


    def test_wheel_preserves_disjoint_mains_and_independent_specials(self):
        output = io.StringIO()
        with patch.object(generator, '_RNG', AscendingEntropy()), contextlib.redirect_stdout(output):
            pool, tickets = generator.generate_covering_wheel(10)
        self.assertEqual(pool, list(range(1, 11)))
        self.assertEqual(tickets, [(1, 2, 3, 4, 5), (6, 7, 8, 9, 10)])
        self.assertFalse(set(tickets[0]) & set(tickets[1]))
        self.assertGreater(generator.distance_squared(tickets[0]), generator.QR80_THRESHOLD)
        # The two printed specials may coincide with one another and with a main number.
        self.assertEqual([int(x) for x in re.findall(r'ĐB:\s*(\d+)', output.getvalue())], [1, 1])

    def test_invalid_generation_counts_cannot_fall_through_to_wheel(self):
        for count in (0, -1, math.comb(35, 5) + 1):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    generator.suggest_uniform(count)
                proc = subprocess.run([sys.executable, str(Path(generator.__file__)), '--gen', str(count)],
                                      capture_output=True, text=True, check=False)
                self.assertNotEqual(proc.returncode, 0)
        proc = subprocess.run([sys.executable, str(Path(generator.__file__)), '--wheel', '0'],
                              capture_output=True, text=True, check=False)
        self.assertNotEqual(proc.returncode, 0)



if __name__ == '__main__':
    unittest.main()
