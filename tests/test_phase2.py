from hughes_forensics.phase2 import first_mypy_failure, stable_seed


def test_first_mypy_failure_returns_tool_result_index() -> None:
    messages = [
        {"role": "assistant", "content": "[Tool call] mypy src/"},
        {"role": "user", "content": "[Tool result]\nFound 4 errors in 2 files"},
        {"role": "assistant", "content": "next"},
    ]
    assert first_mypy_failure(messages) == 1


def test_first_mypy_failure_rejects_non_mypy_errors() -> None:
    messages = [
        {"role": "assistant", "content": "[Tool call] pytest"},
        {"role": "user", "content": "[Tool result]\nFound 4 errors"},
    ]
    assert first_mypy_failure(messages) is None


def test_stable_seed_is_repeatable_and_sensitive_to_parts() -> None:
    assert stable_seed("a", "b") == stable_seed("a", "b")
    assert stable_seed("a", "b") != stable_seed("ab")
