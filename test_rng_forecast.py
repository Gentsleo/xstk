"""Regression checks for forecast chronology, frozen prefixes and QR support."""

from contextlib import redirect_stdout
from io import StringIO
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

import rng_forecast
from rng_lab import load_history, reference


class ForecastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = [dict(draw_id=i, date='01/01/2025', num1=1, num2=2,
                        num3=3, num4=4, num5=5 + i, special=i)
                   for i in range(1, 9)]

    def _call(self, *args):
        with redirect_stdout(StringIO()) as out:
            rng_forecast.main(list(args))
        return json.loads(out.getvalue())

    def test_lock_is_exclusive_and_new_draws_only(self):
        with TemporaryDirectory() as directory:
            path = Path(directory)
            source = path / 'history.json'
            lock = path / 'frozen.json'
            source.write_text(json.dumps(self.raw[:6]), encoding='utf-8')
            options = ('--source', str(source), '--min-train', '4', '--validation', '2')
            locked = self._call(*options, '--lock', str(lock))
            self.assertFalse(locked['evidence']['prospective'])
            self.assertIsNone(locked['test'])
            original_manifest = lock.read_bytes()
            with redirect_stdout(StringIO()), self.assertRaises(SystemExit):
                rng_forecast.main([*options, '--lock', str(lock)])
            self.assertEqual(lock.read_bytes(), original_manifest)
            pending = self._call('--source', str(source), '--prospective', str(lock))
            self.assertEqual(pending['status'], 'pending')
            self.assertFalse(pending['evidence']['prospective'])
            self.assertIsNone(pending['evidence']['log_evalue'])
            source.write_text(json.dumps(self.raw[:8]), encoding='utf-8')
            prospective = self._call('--source', str(source), '--prospective', str(lock))
            self.assertEqual(prospective['status'], 'prospective')
            self.assertEqual(prospective['evidence']['n_new'], 2)
            self.assertEqual(prospective['evaluated_draw_ids'], [self.raw[6]['draw_id'],
                                                                 self.raw[7]['draw_id']])
            self.assertAlmostEqual(prospective['evidence']['log_evalue'], 2 * (
                prospective['test']['uniform']['mean_logloss_joint'] -
                prospective['test'][prospective['selected_model']]['mean_logloss_joint']))
            self.assertEqual(lock.read_bytes(), original_manifest)
            tampered = json.loads(source.read_text(encoding='utf-8'))
            tampered[0]['special'] = tampered[0]['special'] % 12 + 1
            source.write_text(json.dumps(tampered), encoding='utf-8')
            with redirect_stdout(StringIO()), self.assertRaises(SystemExit):
                rng_forecast.main(['--source', str(source), '--prospective', str(lock)])

    def test_ticket_models_are_normalized_and_qr_has_full_support(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / 'history.json'
            source.write_text(json.dumps(self.raw[:6]), encoding='utf-8')
            rows = load_history(source)
            ref = reference()
            outside = tuple(int(x) for x in ref['combos'][int(np.flatnonzero(~ref['inside'])[0])])
            ticket = rng_forecast.report_ticket(rows, outside, 1)
            self.assertFalse(ticket['inside_qr80'])
            self.assertGreater(ticket['models']['qr']['joint'], 0)
            self.assertAlmostEqual(ticket['models']['uniform']['joint'], 1 / (math.comb(35, 5) * 12))
            self.assertAlmostEqual(sum(
                rng_forecast._qr_masses(rng_forecast._state(rows)[2],
                                        rng_forecast._bins()[1], len(rows))), 1.0)
            self.assertIsNone(rng_forecast.report_ticket(rows, outside)['models']['qr']['joint'])
            with self.assertRaises(ValueError):
                rng_forecast.report_ticket(rows, (1, 1, 2, 3, 4), 1)

    def test_first_draw_is_scored_uniformly_before_learning(self):
        first = dict(draw_id=1, date='01/01/2025', combo=(1, 2, 3, 4, 5), special=1)
        second = {**first, 'draw_id': 2}
        score = rng_forecast._evaluate([first, second], rng_forecast._state([]), 535)
        # Independent combinatorial normalizer after observing the first subset.
        w = 1.05
        normalizer = sum(math.comb(5, k) * math.comb(30, 5 - k) * w**k for k in range(6))
        expected_main = (math.log(math.comb(35, 5)) + math.log(normalizer) - 5 * math.log(w)) / 2
        expected_special = (math.log(12) - math.log(6 / 61)) / 2
        self.assertAlmostEqual(score['frequency']['mean_logloss_main'], expected_main)
        self.assertAlmostEqual(score['frequency']['mean_logloss_special'], expected_special)


if __name__ == '__main__':
    unittest.main()
