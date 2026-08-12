from __future__ import annotations

from tests.benchmark.framework import BenchmarkRunner, TestCase, BenchmarkLevel
from tests.benchmark.test_cases import get_benchmark_test_cases, run_benchmark_suite


def test_benchmark_suite_execution() -> None:
    report = run_benchmark_suite()
    assert report["total_tests"] == 25
    assert report["passed_tests"] > 0
    assert report["pass_rate"] > 50.0
    assert "Level 1: Single Action" in report["level_scores"]


def test_single_benchmark_case() -> None:
    runner = BenchmarkRunner()
    case = TestCase(
        id="TC-TEST",
        name="Test Case Single Click",
        level=BenchmarkLevel.LEVEL_1_SINGLE_ACTION,
        goal="click OK",
    )
    result = runner.run_case(case)
    assert result.passed is True
    assert result.score >= 80.0
    assert result.steps == 1
