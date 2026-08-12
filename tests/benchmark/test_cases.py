from __future__ import annotations

from tests.benchmark.framework import BenchmarkLevel, TestCase, BenchmarkRunner


def get_benchmark_test_cases() -> list[TestCase]:
    """Return the suite of 25 benchmark test cases for evaluating RTDA."""

    cases = [
        # --- LEVEL 1: Single Actions ---
        TestCase(
            id="TC-101",
            name="Single Click Action",
            level=BenchmarkLevel.LEVEL_1_SINGLE_ACTION,
            goal="click OK",
        ),
        TestCase(
            id="TC-102",
            name="Single Type Action",
            level=BenchmarkLevel.LEVEL_1_SINGLE_ACTION,
            goal="type Hello World",
        ),
        TestCase(
            id="TC-103",
            name="Single Press Action",
            level=BenchmarkLevel.LEVEL_1_SINGLE_ACTION,
            goal="press enter",
        ),
        TestCase(
            id="TC-104",
            name="Single Hotkey Action",
            level=BenchmarkLevel.LEVEL_1_SINGLE_ACTION,
            goal="hotkey ctrl+c",
        ),
        TestCase(
            id="TC-105",
            name="Single Scroll Down",
            level=BenchmarkLevel.LEVEL_1_SINGLE_ACTION,
            goal="scroll down",
        ),
        TestCase(
            id="TC-106",
            name="Single Scroll Up",
            level=BenchmarkLevel.LEVEL_1_SINGLE_ACTION,
            goal="scroll 5",
        ),
        TestCase(
            id="TC-107",
            name="Inspect State Action",
            level=BenchmarkLevel.LEVEL_1_SINGLE_ACTION,
            goal="inspect",
        ),
        TestCase(
            id="TC-108",
            name="Observe Desktop State",
            level=BenchmarkLevel.LEVEL_1_SINGLE_ACTION,
            goal="observe",
        ),

        # --- LEVEL 2: Multi-Step Sequences ---
        TestCase(
            id="TC-201",
            name="Compound Click and Type",
            level=BenchmarkLevel.LEVEL_2_MULTI_STEP,
            goal="click Search and then type Python",
            max_steps=5,
        ),
        TestCase(
            id="TC-202",
            name="Compound Type and Press Enter",
            level=BenchmarkLevel.LEVEL_2_MULTI_STEP,
            goal="type username and press enter",
            max_steps=5,
        ),
        TestCase(
            id="TC-203",
            name="Navigate and Inspect",
            level=BenchmarkLevel.LEVEL_2_MULTI_STEP,
            goal="navigate notepad and then inspect",
            max_steps=5,
        ),
        TestCase(
            id="TC-204",
            name="Click and Scroll",
            level=BenchmarkLevel.LEVEL_2_MULTI_STEP,
            goal="click File and then scroll down",
            max_steps=5,
        ),
        TestCase(
            id="TC-205",
            name="Multi-Hotkey Combination",
            level=BenchmarkLevel.LEVEL_2_MULTI_STEP,
            goal="hotkey ctrl+a and then hotkey ctrl+c",
            max_steps=5,
        ),
        TestCase(
            id="TC-206",
            name="Sequence with Expected Text Verification",
            level=BenchmarkLevel.LEVEL_2_MULTI_STEP,
            goal="click Save",
            expected_text="Save",
            max_steps=5,
        ),

        # --- LEVEL 3: Multi-Window & Context Switching ---
        TestCase(
            id="TC-301",
            name="Open App and Inspect",
            level=BenchmarkLevel.LEVEL_3_MULTI_WINDOW,
            goal="open calc and then observe",
            max_steps=6,
        ),
        TestCase(
            id="TC-302",
            name="Navigate URL and Verify",
            level=BenchmarkLevel.LEVEL_3_MULTI_WINDOW,
            goal="navigate https://example.com and inspect",
            max_steps=6,
        ),
        TestCase(
            id="TC-303",
            name="Switch Window Focus Sequence",
            level=BenchmarkLevel.LEVEL_3_MULTI_WINDOW,
            goal="inspect and then press escape",
            max_steps=6,
        ),
        TestCase(
            id="TC-304",
            name="Form Selection and Input",
            level=BenchmarkLevel.LEVEL_3_MULTI_WINDOW,
            goal="click Input and type test@example.com",
            max_steps=6,
        ),
        TestCase(
            id="TC-305",
            name="Window Hotkey Management",
            level=BenchmarkLevel.LEVEL_3_MULTI_WINDOW,
            goal="hotkey alt+tab and then inspect",
            max_steps=6,
        ),

        # --- LEVEL 4: Complex Workflows & Recovery ---
        TestCase(
            id="TC-401",
            name="Long Sequence Workflow (5 Steps)",
            level=BenchmarkLevel.LEVEL_4_COMPLEX_WORKFLOW,
            goal="click Edit; type Sample Text; hotkey ctrl+s; press enter; inspect",
            max_steps=10,
        ),
        TestCase(
            id="TC-402",
            name="Non-existent Element Recovery Test",
            level=BenchmarkLevel.LEVEL_4_COMPLEX_WORKFLOW,
            goal="click NonExistentButton_XYZ_999",
            max_steps=5,
        ),
        TestCase(
            id="TC-403",
            name="Fallback Exploration Sequence",
            level=BenchmarkLevel.LEVEL_4_COMPLEX_WORKFLOW,
            goal="do something undefined on screen",
            max_steps=5,
        ),
        TestCase(
            id="TC-404",
            name="Safety Policy Evaluation",
            level=BenchmarkLevel.LEVEL_4_COMPLEX_WORKFLOW,
            goal="click Cancel; inspect",
            max_steps=5,
        ),
        TestCase(
            id="TC-405",
            name="End-to-End Responsive Loop",
            level=BenchmarkLevel.LEVEL_4_COMPLEX_WORKFLOW,
            goal="inspect and then scroll down and then inspect",
            max_steps=8,
        ),
        TestCase(
            id="TC-406",
            name="Multi-step Form Submission Simulation",
            level=BenchmarkLevel.LEVEL_4_COMPLEX_WORKFLOW,
            goal="type John Doe and then press tab and then type Admin",
            max_steps=8,
        ),
    ]

    return cases


def run_benchmark_suite() -> dict:
    """Run the benchmark suite and return a dictionary report."""
    runner = BenchmarkRunner()
    cases = get_benchmark_test_cases()
    result = runner.run_suite(cases)

    return {
        "total_tests": result.total_tests,
        "passed_tests": result.passed_tests,
        "failed_tests": result.failed_tests,
        "pass_rate": result.pass_rate,
        "overall_score": result.overall_score,
        "total_elapsed_ms": result.total_elapsed_ms,
        "avg_task_latency_ms": result.avg_task_latency_ms,
        "level_scores": result.level_scores,
        "results": [
            {
                "id": r.case_id,
                "name": r.name,
                "level": r.level.value,
                "passed": r.passed,
                "score": r.score,
                "steps": r.steps,
                "elapsed_ms": r.elapsed_ms,
                "stop_reason": r.stop_reason,
                "error": r.error,
                "telemetry": r.telemetry,
            }
            for r in result.test_results
        ],
    }
