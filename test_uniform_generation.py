"""Behavioral checks for the frozen model gate and the explicit uniform baseline."""

import contextlib
from itertools import combinations
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
    """Drive uniform Random.sample toward an extreme but valid main combination."""

    def __init__(self):
        super().__init__(0)
        self.position = 0

    def _randbelow(self, n):
        if n == 12:
            return 0
        position = self.position
        self.position += 1
        return position


class SpecialOne(random.Random):
    """Choose special 1 for every ticket without changing main sampling."""

    def randrange(self, *args, **kwargs):
        return 1


class ModelGenerationTests(unittest.TestCase):
    @staticmethod
    def accepted_with_and_without_one():
        with_one = without_one = None
        for combo in combinations(range(1, 36), 5):
            if generator.score_main(combo)["model_accepted"]:
                if 1 in combo and with_one is None:
                    with_one = combo
                elif 1 not in combo and without_one is None:
                    without_one = combo
                if with_one and without_one:
                    return with_one, without_one
        raise AssertionError("Model has no accepted mains with and without 1")

    def test_model_gate_scores_and_unique_mains(self):
        with patch.object(generator, '_RNG', random.Random(17)):
            rows = generator.suggest_model(20)
        mains = [tuple(row["combo"]) for row in rows]
        self.assertEqual(len(mains), len(set(mains)))
        for main, row in zip(mains, rows):
            scored = generator.score_main(main)
            self.assertTrue(scored["model_accepted"])
            self.assertGreaterEqual(scored["sqs"], generator.MIN_SQS)
            self.assertGreaterEqual(scored["gap_entropy"], generator.MIN_ENTROPY)
            self.assertEqual(row["sqs"], scored["sqs"])
            self.assertTrue(row["model_accepted"])
            self.assertTrue(1 <= row["special_info"]["special"] <= 12)
            self.assertEqual(row["in_qr80"],
                             generator.distance_squared(main) <= generator.QR80_THRESHOLD)

    def test_duplicates_rejected_and_special_selected_after_main(self):
        with_one, without_one = self.accepted_with_and_without_one()
        outside = (1, 2, 3, 4, 5)
        self.assertFalse(generator.score_main(outside)["model_accepted"])
        with patch.object(generator, "sample_uniform_ticket",
                          side_effect=[outside, with_one, with_one, without_one]), \
             patch.object(generator, "_RNG", SpecialOne(7)):
            rows = generator.suggest_model(2)
        self.assertEqual([tuple(row["combo"]) for row in rows], [with_one, without_one])
        self.assertEqual([row["special_info"]["special"] for row in rows], [1, 1])
        self.assertTrue(rows[0]["special_info"]["is_overlap"])
        self.assertFalse(rows[1]["special_info"]["is_overlap"])

    def test_bounded_failure_never_returns_unfiltered_or_partial(self):
        accepted, _ = self.accepted_with_and_without_one()
        outside = (1, 2, 3, 4, 5)
        with patch.object(generator, "_MAX_ATTEMPTS_PER_TICKET", 4), \
             patch.object(generator, "sample_uniform_ticket",
                          side_effect=[accepted] + [outside] * 7):
            with self.assertRaises(RuntimeError):
                generator.suggest_model(2)

    def test_wheel_exhaustion_is_explicit(self):
        accepted, _ = self.accepted_with_and_without_one()
        with patch.object(generator, "_MAX_WHEEL_ATTEMPTS", 3), \
             patch.object(generator, "sample_uniform_ticket", return_value=accepted):
            with self.assertRaises(RuntimeError):
                generator.generate_covering_wheel(10)

    def test_wheel_disjoint_accepted_and_independent_specials(self):
        output = io.StringIO()
        with patch.object(generator, "_RNG", SpecialOne(17)), \
             contextlib.redirect_stdout(output):
            pool, tickets = generator.generate_covering_wheel(10)
        self.assertEqual(len(pool), 10)
        self.assertEqual(len(set(pool)), 10)
        self.assertEqual(len(tickets), 2)
        self.assertFalse(set(tickets[0]) & set(tickets[1]))
        self.assertTrue(all(generator.score_main(ticket)["model_accepted"]
                            for ticket in tickets))
        # The special draw is permitted to repeat across tickets and overlap mains.
        self.assertEqual([int(x) for x in re.findall(r'ĐB:\s*(\d+)', output.getvalue())],
                         [1, 1])

    def test_invalid_counts(self):
        for count in (0, -1, generator.MAX_SUGGESTIONS + 1):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    generator.suggest_model(count)
                proc = subprocess.run([sys.executable, str(Path(generator.__file__)),
                                       "--gen", str(count)],
                                      capture_output=True, text=True, check=False)
                self.assertNotEqual(proc.returncode, 0)
        with self.assertRaises(ValueError):
            generator.generate_covering_wheel(0)

    def test_uniform_research_baseline_retains_full_support_and_bounds(self):
        outside = (1, 2, 3, 4, 5)
        self.assertGreater(generator.distance_squared(outside), generator.QR80_THRESHOLD)
        with patch.object(generator, "_RNG", AscendingEntropy()):
            self.assertEqual(generator.sample_uniform_ticket(), outside)
        with patch.object(generator, "_RNG", AscendingEntropy()):
            result = generator.suggest_uniform(1)[0]
        self.assertEqual(tuple(result["combo"]), outside)
        self.assertFalse(result["in_qr80"])
        self.assertEqual(result["special_info"]["special"], 1)
        for count in (0, -1, math.comb(35, 5) + 1):
            with self.assertRaises(ValueError):
                generator.suggest_uniform(count)


if __name__ == '__main__':
    unittest.main()
