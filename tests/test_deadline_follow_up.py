from datetime import date

from legal_image_pipeline import LegalImagePipeline, MatterImageRequest


def test_deadline_window_controls_generation_and_storage(tmp_path):
    calls: list[tuple[str, str]] = []

    def generate(prompt: str, idempotency_key: str) -> bytes:
        calls.append((prompt, idempotency_key))
        return b"generated-png"

    pipeline = LegalImagePipeline(tmp_path, generate)
    outside_window = MatterImageRequest(
        matter_id="MAT-204",
        client_name="Rivera Holdings",
        stage="deadline_follow_up",
        deadline=date(2026, 9, 1),
    )
    due_soon = outside_window.model_copy(update={"deadline": date(2026, 8, 20)})

    skipped = pipeline.run(outside_window, today=date(2026, 8, 12))
    stored = pipeline.run(due_soon, today=date(2026, 8, 16))

    assert skipped.generated is False
    assert skipped.reason == "deadline is outside the seven-day follow-up window"
    assert stored.generated is True
    assert stored.image_path is not None
    assert len(calls) == 1
    assert "due in 4 days" in calls[0][0]
    assert calls[0][1] == "MAT-204:deadline_follow_up:2026-08-20"
    assert (tmp_path / stored.image_path.split("/")[-1]).read_bytes() == b"generated-png"
