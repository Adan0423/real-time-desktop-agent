from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Any

from rtda.agent.executor import AgentExecutor, AgentTaskResult
from rtda.models.actions import ActionResult, ActionStatus


class BenchmarkLevel(Enum):
    LEVEL_1_SINGLE_ACTION = "Level 1: Single Action"
    LEVEL_2_MULTI_STEP = "Level 2: Multi-Step"
    LEVEL_3_MULTI_WINDOW = "Level 3: Multi-Window"
    LEVEL_4_COMPLEX_WORKFLOW = "Level 4: Complex Workflow"


@dataclass
class TestCase:
    __test__ = False
    id: str
    name: str
    level: BenchmarkLevel
    goal: str
    expected_text: str | None = None
    setup_fn: Callable[[], None] | None = None
    teardown_fn: Callable[[], None] | None = None
    max_steps: int = 10
    dry_run: bool = True


@dataclass
class TestCaseResult:
    case_id: str
    name: str
    level: BenchmarkLevel
    passed: bool
    score: float  # 0.0 - 100.0
    steps: int
    elapsed_ms: float
    stop_reason: str
    telemetry: dict[str, float] = field(default_factory=dict)
    error: str | None = None


@dataclass
class BenchmarkSuiteResult:
    total_tests: int
    passed_tests: int
    failed_tests: int
    pass_rate: float
    overall_score: float
    total_elapsed_ms: float
    avg_task_latency_ms: float
    level_scores: dict[str, float] = field(default_factory=dict)
    test_results: list[TestCaseResult] = field(default_factory=list)


class BenchmarkRunner:
    def __init__(self, executor: AgentExecutor | None = None) -> None:
        self.executor = executor or AgentExecutor()

    def run_case(self, case: TestCase) -> TestCaseResult:
        if case.setup_fn:
            try:
                case.setup_fn()
            except Exception as exc:
                return TestCaseResult(
                    case_id=case.id,
                    name=case.name,
                    level=case.level,
                    passed=False,
                    score=0.0,
                    steps=0,
                    elapsed_ms=0.0,
                    stop_reason="setup_failed",
                    error=f"Setup failed: {exc}",
                )

        t0 = time.perf_counter()
        try:
            task_result: AgentTaskResult = self.executor.run_task(
                goal=case.goal,
                max_steps=case.max_steps,
                expected_text=case.expected_text,
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            # Score calculation based on success, steps efficiency, and latency
            score = 0.0
            if task_result.success:
                score = 80.0  # Base pass score
                # Step efficiency bonus (up to 10 points)
                if task_result.steps <= 3:
                    score += 10.0
                elif task_result.steps <= 5:
                    score += 5.0

                # Latency efficiency bonus (up to 10 points)
                if task_result.elapsed_ms < 500:
                    score += 10.0
                elif task_result.elapsed_ms < 1500:
                    score += 5.0

            return TestCaseResult(
                case_id=case.id,
                name=case.name,
                level=case.level,
                passed=task_result.success,
                score=round(score, 1),
                steps=task_result.steps,
                elapsed_ms=round(elapsed_ms, 2),
                stop_reason=task_result.stop_reason,
                telemetry=task_result.telemetry,
            )
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return TestCaseResult(
                case_id=case.id,
                name=case.name,
                level=case.level,
                passed=False,
                score=0.0,
                steps=0,
                elapsed_ms=round(elapsed_ms, 2),
                stop_reason="exception",
                error=str(exc),
            )
        finally:
            if case.teardown_fn:
                try:
                    case.teardown_fn()
                except Exception:
                    pass

    def run_suite(self, cases: list[TestCase]) -> BenchmarkSuiteResult:
        t0 = time.perf_counter()
        results: list[TestCaseResult] = []

        level_totals: dict[str, list[float]] = {}

        for case in cases:
            res = self.run_case(case)
            results.append(res)

            lvl_name = case.level.value
            if lvl_name not in level_totals:
                level_totals[lvl_name] = []
            level_totals[lvl_name].append(res.score)

        total_elapsed_ms = (time.perf_counter() - t0) * 1000.0
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        pass_rate = round((passed / total) * 100.0, 1) if total > 0 else 0.0

        scores = [r.score for r in results]
        overall_score = round(sum(scores) / len(scores), 1) if scores else 0.0
        avg_latency = round(sum(r.elapsed_ms for r in results) / len(results), 1) if results else 0.0

        level_scores = {
            lvl: round(sum(scs) / len(scs), 1) for lvl, scs in level_totals.items() if scs
        }

        return BenchmarkSuiteResult(
            total_tests=total,
            passed_tests=passed,
            failed_tests=total - passed,
            pass_rate=pass_rate,
            overall_score=overall_score,
            total_elapsed_ms=round(total_elapsed_ms, 2),
            avg_task_latency_ms=avg_latency,
            level_scores=level_scores,
            test_results=results,
        )
