"""Consumer-visible combinatorial, fault and statistical invariants."""
import tempfile
from pathlib import Path
import json
import unittest

import numpy as np

import rng_lab as lab
from qr_filter import QR80_SIZE, distance_squared


class ReferenceTests(unittest.TestCase):
    def test_all_subset_ranks_are_bijective(self):
        ref = lab.reference()
        np.testing.assert_array_equal(lab.rank_combos(ref['combos']), np.arange(lab.TOTAL))
        self.assertEqual(int(ref['inside'].sum()), QR80_SIZE)
        self.assertEqual(int(ref['bin_counts'].sum()), lab.TOTAL)
        # Check difficult cutoffs, not just typical examples.
        for index in np.argsort(abs(ref['d2'] - lab.QR80_THRESHOLD))[:20]:
            self.assertAlmostEqual(ref['d2'][index], distance_squared(ref['combos'][index]), places=12)

    def test_ticket_probability_does_not_reward_qr_membership(self):
        ref = lab.reference()
        inner = ref['combos'][np.flatnonzero(ref['inside'])[0]].tolist()
        outer = ref['combos'][np.flatnonzero(~ref['inside'])[0]].tolist()
        a, b = lab.ticket_report(inner + [1]), lab.ticket_report(outer + [1])
        self.assertTrue(a['inside_qr80'])
        self.assertFalse(b['inside_qr80'])
        self.assertEqual(a['fair_5plus1_probability'], b['fair_5plus1_probability'])
        with self.assertRaises(ValueError):
            lab.ticket_report([1, 1, 2, 3, 4])
        with self.assertRaises(ValueError):
            lab.ticket_report([1, 2, 3, 4, 5, 13])


class FaultTests(unittest.TestCase):
    def test_fault_support_and_reset_boundaries(self):
        ref = lab.reference()
        for model in lab.MODELS:
            sim = lab.Simulator(model, 1., 15)
            a, sp = sim.generate(91)
            self.assertTrue(np.all((a >= 0) & (a < lab.TOTAL)), model)
            self.assertTrue(np.all((sp >= 1) & (sp <= 12)), model)
            if model == 'B1':
                self.assertTrue(np.all(ref['combos'][a, 0] == 1))
            elif model == 'B3':
                self.assertTrue(np.all(a == a[0]))
            elif model == 'B4':
                self.assertTrue(np.array_equal(a[16:], a[:-16]))
                # Continue across an unaligned chunk: resets must follow global draw position.
                b, bsp = sim.generate(29)
                stream = np.concatenate([a, b])
                spstream = np.concatenate([sp, bsp])
                self.assertTrue(np.array_equal(stream[16:], stream[:-16]))
                self.assertTrue(np.array_equal(spstream[16:], spstream[:-16]))
            elif model == 'B5':
                self.assertTrue(np.all(ref['inside'][a]))

    def test_familywise_ties_are_not_false_evidence(self):
        bank = np.zeros((99, 5))
        calibration = np.zeros((99, 5))
        # Every statistic tied with every fair draw must produce p=1.
        p = lab.global_p(np.zeros(5), calibration, lab.omnibus(bank, calibration))
        self.assertEqual(float(p[0]), 1.)
        # Conservative Monte Carlo resolution never reports p=0.
        p = lab.global_p(np.ones(5), calibration, lab.omnibus(bank, calibration))
        self.assertEqual(float(p[0]), .01)

    def test_reproducible_stream_preserves_number_of_draws(self):
        a = lab.simulate(1003, 117, 'uniform', 0., 23)
        b = lab.simulate(1003, 117, 'uniform', 0., 23)
        self.assertEqual(a['stream_sha256'], b['stream_sha256'])
        self.assertEqual(sum(a['main_counts']), 5 * 1003)
        self.assertEqual(sum(a['special_counts']), 1003)


class HistoryTests(unittest.TestCase):
    def test_missing_ids_and_invalid_special_are_rejected(self):
        rows = [dict(draw_id=i, date='01/01/2025', num1=1, num2=2, num3=3,
                     num4=4, num5=5, special=1) for i in (1, 3)]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'history.json'
            path.write_text(json.dumps(rows))
            with self.assertRaisesRegex(ValueError, 'Missing draw IDs'):
                lab.load_history(path)
            rows[1]['draw_id'] = 2
            rows[1]['special'] = 13
            path.write_text(json.dumps(rows))
            with self.assertRaisesRegex(ValueError, 'Invalid special'):
                lab.load_history(path)


if __name__ == '__main__':
    unittest.main()
