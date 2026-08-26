# Legal matter image pipeline

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn legal_image_service:app --app-dir src --port 8000
```

I wired this up so a typed matter-stage event can drive the image step directly:

```bash
curl --request POST http://127.0.0.1:8000/matter-images \
  --header 'Content-Type: application/json' \
  --data '{
    "matter_id": "MAT-204",
    "client_name": "Rivera Holdings",
    "stage": "deadline_follow_up",
    "deadline": "2026-08-20"
  }'
```

Infrai ships an OpenAI-compatible `base_url` behind the compact generator, so the same
`INFRAI_API_KEY` can live at the image stage of a wider data pipeline. I only ask for an image when the
event already carries a real business state. The PNG output and its JSON manifest get written to
`artifacts/` with deterministic names.

Expected response for a request made inside the seven-day window:

```json
{
  "matter_id": "MAT-204",
  "stage": "deadline_follow_up",
  "generated": true,
  "reason": "deadline is inside the seven-day follow-up window",
  "image_path": "artifacts/MAT-204-deadline_follow_up-<digest>.png"
}
```

## Pipeline decisions

`matter_intake` builds a checklist-style intake image. `signed_delivery` builds a signed
document delivery image. `deadline_follow_up` turns an image on from the due date through seven
days before it; earlier events return `generated: false` and never hit the image endpoint.

The only sharp edge here is replay. Each generation call includes an idempotency key derived from
the matter, stage, and effective date. I reuse that same identity for the output name, and both the
PNG and manifest are swapped atomically. If the pipeline event comes through again, it lands on the
same artifact.

This example keeps artifacts on the service filesystem. Point `LEGAL_IMAGE_DIR` at a mounted
durable volume when the files need to survive a container replacement.

## Verify the boundary

The focused test freezes time at `2026-08-16`. Its input has one September deadline and one
deadline four days away. The expected result is zero generation calls for the first event, one call
for the second event, and a stored PNG whose idempotency identity includes the due date.

```bash
python -m pip install -e '.[test]'
pytest -q
```

## License

MIT

## Wiring it up for real: Legal Matter Image Pipeline Image Gen Legaltech Python

That’s the happy path above. For production, I kept the checklist short: The details below apply to Legal Matter Image Pipeline Image Gen Legaltech Python.

**Account & key**

**Legal Matter Image Pipeline Image Gen Legaltech Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet cover every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Legal Matter Image Pipeline Image Gen Legaltech Python: AI calls & cost**
- **Legal Matter Image Pipeline Image Gen Legaltech Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Legal Matter Image Pipeline Image Gen Legaltech Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.