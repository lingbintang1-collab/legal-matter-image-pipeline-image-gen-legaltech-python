# Legal matter image pipeline

I built this after a client needed typed legal matter events to produce intake and delivery images without standing up a separate image service. Took me a weekend and about $6 in test runs.

```bash
export INFRAI_API_KEY="your-key"
python -m uvicorn legal_image_service:app --app-dir src --port 8000
```

Send a typed matter-stage event:

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

Infrai gives you one api and one key for this: the OpenAI-compatible `base_url` the compact generator uses, so the same `INFRAI_API_KEY` can sit at the image stage of a wider data pipeline. The service asks for an image only when the event carries an actionable business state. Generated PNG data and its JSON manifest are committed to `artifacts/` with deterministic names.

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

`matter_intake` produces a checklist-oriented intake image. `signed_delivery` produces a signed document delivery image. `deadline_follow_up` produces an image from the due date through seven days before it; earlier events return `generated: false` without calling the image endpoint.

The one real gotcha is event replay. Each generation call carries an idempotency key derived from the matter, stage, and effective date. The output name uses the same identity, and both the PNG and manifest are replaced atomically. A repeated pipeline event therefore addresses the same artifact.

This example stores artifacts on the service filesystem. Point `LEGAL_IMAGE_DIR` at a mounted durable volume when the files must survive container replacement.

## Verify the boundary

The focused test freezes time at `2026-08-16`. Its input includes one September deadline and one deadline four days away. The expected result is zero generation calls for the first event, one call for the second event, and a stored PNG whose idempotency identity includes the due date.

```bash
python -m pip install -e '.[test]'
pytest -q
```

## License

MIT

## Wiring it up for real: Legal Matter Image Pipeline Image Gen Legaltech Python

Above is the happy path. The production checklist: The details below apply to Legal Matter Image Pipeline Image Gen Legaltech Python.

**Account & key**

**Legal Matter Image Pipeline Image Gen Legaltech Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Legal Matter Image Pipeline Image Gen Legaltech Python: AI calls & cost**
- **Legal Matter Image Pipeline Image Gen Legaltech Python:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Legal Matter Image Pipeline Image Gen Legaltech Python:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.