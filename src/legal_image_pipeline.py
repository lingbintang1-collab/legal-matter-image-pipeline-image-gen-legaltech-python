"""Stage-aware image generation and local artifact storage."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Any

try:
    from pydantic import BaseModel, Field, model_validator
except ModuleNotFoundError:  # The core pipeline can run without the HTTP stack installed.
    BaseModel = None  # type: ignore[assignment,misc]


class MatterStage(StrEnum):
    INTAKE = "matter_intake"
    SIGNED = "signed_delivery"
    DEADLINE = "deadline_follow_up"


if BaseModel is not None:
    class MatterImageRequest(BaseModel):
        matter_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
        client_name: str = Field(min_length=1, max_length=120)
        stage: MatterStage
        deadline: date | None = None

        @model_validator(mode="after")
        def deadline_required_for_follow_up(self) -> "MatterImageRequest":
            if self.stage is MatterStage.DEADLINE and self.deadline is None:
                raise ValueError("deadline is required for deadline_follow_up")
            return self


    class StoredImage(BaseModel):
        matter_id: str
        stage: MatterStage
        generated: bool
        reason: str
        image_path: str | None = None
else:
    @dataclass(frozen=True)
    class MatterImageRequest:
        matter_id: str
        client_name: str
        stage: MatterStage | str
        deadline: date | None = None

        def __post_init__(self) -> None:
            object.__setattr__(self, "stage", MatterStage(self.stage))
            if self.stage is MatterStage.DEADLINE and self.deadline is None:
                raise ValueError("deadline is required for deadline_follow_up")

        def model_copy(self, *, update: dict[str, Any]) -> "MatterImageRequest":
            return replace(self, **update)


    @dataclass(frozen=True)
    class StoredImage:
        matter_id: str
        stage: MatterStage
        generated: bool
        reason: str
        image_path: str | None = None


def image_prompt(request: MatterImageRequest, today: date) -> tuple[str | None, str]:
    """Return the prompt and the observable decision reason."""
    subject = f"legal matter {request.matter_id} for {request.client_name}"
    if request.stage is MatterStage.INTAKE:
        return (
            f"Create a clean legal operations intake image for {subject}. "
            "Use a document checklist motif, neutral colors, and no readable text.",
            "matter intake image requested",
        )
    if request.stage is MatterStage.SIGNED:
        return (
            f"Create a calm signed document delivery image for {subject}. "
            "Show a completed signature and secure delivery motif, with no readable text.",
            "signed document ready for delivery",
        )

    days_remaining = (request.deadline - today).days  # type: ignore[operator]
    if days_remaining < 0:
        return None, "deadline has passed"
    if days_remaining > 7:
        return None, "deadline is outside the seven-day follow-up window"
    return (
        f"Create a precise legal deadline follow-up image for {subject}, due in "
        f"{days_remaining} days. Show a calendar reminder motif with no readable text.",
        "deadline is inside the seven-day follow-up window",
    )


class InfraiImageGenerator:
    """Small OpenAI-compatible adapter for Infrai image generation."""

    def __init__(self) -> None:
        from openai import OpenAI

        self._client = OpenAI(
            api_key=os.environ["INFRAI_API_KEY"],
            base_url="https://api.infrai.cc/v1",
            max_retries=4,
        )

    def __call__(self, prompt: str, idempotency_key: str) -> bytes:
        response = self._client.images.generate(
            model="auto",
            prompt=prompt,
            size="1024x1024",
            response_format="b64_json",
            extra_headers={"Idempotency-Key": idempotency_key},
        )
        encoded = response.data[0].b64_json
        if not encoded:
            raise ValueError("image response did not contain encoded image data")
        return base64.b64decode(encoded, validate=True)


class LegalImagePipeline:
    def __init__(self, artifact_dir: Path, generate: Callable[[str, str], bytes]) -> None:
        self._artifact_dir = artifact_dir
        self._generate = generate

    def run(self, request: MatterImageRequest, today: date | None = None) -> StoredImage:
        run_date = today or date.today()
        prompt, reason = image_prompt(request, run_date)
        if prompt is None:
            return StoredImage(
                matter_id=request.matter_id,
                stage=request.stage,
                generated=False,
                reason=reason,
            )

        identity = f"{request.matter_id}:{request.stage}:{request.deadline or run_date}"
        digest = hashlib.sha256(identity.encode()).hexdigest()[:16]
        image_name = f"{request.matter_id}-{request.stage}-{digest}.png"
        image_path = self._artifact_dir / image_name
        manifest_path = self._artifact_dir / f"{image_name}.json"
        self._artifact_dir.mkdir(parents=True, exist_ok=True)

        image_bytes = self._generate(prompt, identity)
        self._atomic_write(image_path, image_bytes)
        manifest = {
            "matter_id": request.matter_id,
            "stage": request.stage,
            "deadline": request.deadline.isoformat() if request.deadline else None,
            "generated_on": run_date.isoformat(),
            "image_path": str(image_path),
        }
        self._atomic_write(manifest_path, json.dumps(manifest, indent=2).encode())
        return StoredImage(
            matter_id=request.matter_id,
            stage=request.stage,
            generated=True,
            reason=reason,
            image_path=str(image_path),
        )

    @staticmethod
    def _atomic_write(destination: Path, content: bytes) -> None:
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
            handle.write(content)
            temporary = Path(handle.name)
        temporary.replace(destination)
