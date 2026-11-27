"""Behavioral checks for the official detail-page update fallback."""

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import auto_update as updater


DETAIL_PAGE = """
<div class="chitietketqua_title">
  <h5>Kỳ quay thưởng <b>#01033</b> ngày <b>27/11/2026</b></h5>
</div>
<div class="day_so_ket_qua_v2">
  <span class="bong_tron small">03</span>
  <span class="bong_tron small">12</span>
  <span class="bong_tron small">18</span>
  <span class="bong_tron small">28</span>
  <span class="bong_tron small">33</span>
  <span class="bong_tron small no-margin-right active">07</span>
</div>
"""


class DetailPageParsingTests(unittest.TestCase):
    def test_parses_a_matching_official_draw(self):
        self.assertEqual(
            updater.parse_detail_draw_page(DETAIL_PAGE, 1033),
            {
                "draw_id": 1033,
                "draw_code": "01033",
                "date": "27/11/2026",
                "num1": 3,
                "num2": 12,
                "num3": 18,
                "num4": 28,
                "num5": 33,
                "special": 7,
                "numbers_str": "03 12 18 28 33 | 07",
            },
        )

    def test_treats_explicitly_missing_draw_as_end_of_results(self):
        self.assertIsNone(
            updater.parse_detail_draw_page("<body>Không tìm thấy kết quả [01034]</body>", 1034)
        )

    def test_rejects_a_page_for_the_wrong_draw(self):
        with self.assertRaisesRegex(ValueError, "expected #01032"):
            updater.parse_detail_draw_page(DETAIL_PAGE, 1032)



class GitHubActionErrorTests(unittest.TestCase):
    def test_emits_an_escaped_github_error_annotation(self):
        output = io.StringIO()
        with patch.dict(updater.os.environ, {"GITHUB_ACTIONS": "true"}):
            with redirect_stdout(output):
                updater.report_github_action_error("listing 403%\r\nfallback")

        self.assertEqual(
            output.getvalue(),
            "::error title=Official results unavailable::listing 403%25%0D%0Afallback\n",
        )

    def test_is_silent_outside_github_actions(self):
        output = io.StringIO()
        with patch.dict(updater.os.environ, {"GITHUB_ACTIONS": "false"}):
            with redirect_stdout(output):
                updater.report_github_action_error("source unavailable")

        self.assertEqual(output.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
