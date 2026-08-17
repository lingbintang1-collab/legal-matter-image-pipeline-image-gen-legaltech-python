"""Typed HTTP boundary for the legal image pipeline."""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from openai import APIConnectionError, APIStatusError

from legal_image_pipeline import (
    InfraiImageGenerator,
    LegalImagePipeline,
    MatterImageRequest,
    StoredImage,
)

app = FastAPI(title="Legal matter image pipeline")


def build_pipeline() -> LegalImagePipeline:
    artifact_dir = Path(os.environ.get("LEGAL_IMAGE_DIR", "artifacts"))
    return LegalImagePipeline(artifact_dir, InfraiImageGenerator())


@app.post("/matter-images", response_model=StoredImage)
def create_matter_image(request: MatterImageRequest) -> StoredImage:
    try:
        return build_pipeline().run(request)
    except APIStatusError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    except APIConnectionError as exc:
        raise HTTPException(status_code=502, detail="image provider connection failed") from exc
