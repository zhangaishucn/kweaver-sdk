#!/usr/bin/env bash
# Unified test runner for KWeaver SDK
#
# Usage: tests/run_tests.sh <test_type> [pytest options]
#   test_type: unit | integration | e2e | all (all = unit + integration)
#
# Examples:
#   tests/run_tests.sh unit                              # SDK resource tests
#   tests/run_tests.sh integration                       # Skill orchestration tests
#   tests/run_tests.sh e2e                               # Read-only E2E tests
#   tests/run_tests.sh e2e --run-destructive             # Including build/delete tests
#   tests/run_tests.sh e2e --e2e-base-url https://...    # Override KWeaver URL
#   tests/run_tests.sh all -v                            # Verbose unit + integration

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

TYPE="${1:-all}"
shift || true

run_unit() {
    echo "═══ Running Unit Tests ═══"
    pytest tests/unit/ "$@"
}

run_integration() {
    echo "═══ Running Integration Tests ═══"
    pytest tests/integration/ "$@"
}

run_e2e() {
    echo "═══ Running E2E Tests ═══"
    pytest tests/e2e/ "$@"
}

case "${TYPE}" in
    unit)
        run_unit "$@"
        ;;
    integration)
        run_integration "$@"
        ;;
    e2e)
        run_e2e "$@"
        ;;
    all)
        run_unit "$@"
        run_integration "$@"
        ;;
    *)
        echo "Usage: $0 {unit|integration|e2e|all} [pytest options]"
        exit 1
        ;;
esac
