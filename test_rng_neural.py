"""Neural provenance and lagged-feature regressions; no PyTorch dependency."""
import unittest

import numpy as np

from rng_lab import history_digest
from rng_neural import MIN_NEW, _dataset, _gate, _reference_bins, _synthetic


class NeuralSafetyTests(unittest.TestCase):

    def test_lag_features_exclude_current_target(self):
        rows = _synthetic(132, 17)
        bins, _, _ = _reference_bins()
        features_before, _, _ = _dataset(rows, bins)
        rows[-1] = {**rows[-1], 'combo': (1, 2, 3, 4, 5), 'special': 12}
        features_after, _, _ = _dataset(rows, bins)
        np.testing.assert_array_equal(features_before, features_after)

    def test_retrospective_report_cannot_open_training_gate(self):
        rows = _synthetic(MIN_NEW + 33, 23)
        digest = history_digest(rows)
        template = {'mode': 'retrospective', 'status': 'retrospective',
                    'history_sha256': digest, 'locked_prefix_sha256': history_digest(rows[:-MIN_NEW]),
                    'locked_last_draw_id': rows[-MIN_NEW - 1]['draw_id'],
                    'selected_model': 'frequency',
                    'evidence': {'prospective': False, 'prefix_verified': True,
                                 'selected_model': 'frequency', 'n_new': MIN_NEW,
                                 'log_evalue': 100.0}}
        from tempfile import TemporaryDirectory
        import json
        from pathlib import Path
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'report.json'
            path.write_text(json.dumps(template), encoding='utf-8')
            allowed, _ = _gate(path, rows, digest)
            self.assertFalse(allowed)
            template['mode'] = 'prospective'
            template['status'] = 'prospective'
            template['evidence']['prospective'] = True
            template['history_sha256'] = '0' * 64
            path.write_text(json.dumps(template), encoding='utf-8')
            allowed, _ = _gate(path, rows, digest)
            self.assertFalse(allowed)

    def test_gate_requires_new_draw_count_and_consistent_likelihood(self):
        import json
        import math
        from pathlib import Path
        from tempfile import TemporaryDirectory
        rows = _synthetic(232, 535)
        n = 100
        fair = math.log(324632 * 12)
        log_e = math.log(25)
        report = {
            'mode': 'prospective', 'status': 'prospective',
            'selected_model': 'qr', 'history_sha256': history_digest(rows),
            'locked_prefix_sha256': history_digest(rows[:-n]),
            'locked_last_draw_id': rows[-n - 1]['draw_id'],
            'history_draws': len(rows), 'evaluated_draws': n,
            'evaluated_draw_ids': [rows[-n]['draw_id'], rows[-1]['draw_id']],
            'evidence': {'prospective': True, 'prefix_verified': True,
                         'selected_model': 'qr', 'n_new': n, 'log_evalue': log_e},
            'test': {'qr': {'draws': n, 'mean_logloss_joint': fair - log_e / n},
                     'uniform': {'draws': n, 'mean_logloss_joint': fair}},
        }
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'report.json'
            def check():
                path.write_text(json.dumps(report), encoding='utf-8')
                return _gate(path, rows, history_digest(rows))[0]
            self.assertTrue(check())
            report['evidence']['n_new'] = 99
            self.assertFalse(check())
            report['evidence']['n_new'] = n
            report['evidence']['log_evalue'] = math.log(100)
            self.assertFalse(check())


if __name__ == '__main__':
    unittest.main()
