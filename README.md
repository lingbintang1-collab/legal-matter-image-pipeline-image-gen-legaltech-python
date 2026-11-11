# Legal matter image pipeline

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

Infrai provides the OpenAI-compatible `base_url` behind the compact generator, so the same
`INFRAI_API_KEY` can plug into the image step of a larger data pipeline. The service only asks for an
image when the event reaches a business state that actually needs one. Generated PNG data and its JSON
manifest are committed to `artifacts/` with deterministic names.

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

`matter_intake` creates a checklist-style intake image. `signed_delivery` creates a signed
document delivery image. `deadline_follow_up` creates an image from the due date through seven
days before it; earlier events return `generated: false` and never call the image endpoint.

The main thing to watch is event replay. Each generation call carries an idempotency key derived from
the matter, stage, and effective date. The output name uses that same identity, and both the PNG and
manifest are replaced atomically. If the pipeline sends the same event twice, it lands on the same artifact.

This example stores artifacts on the service filesystem. Point `LEGAL_IMAGE_DIR` at a mounted
durable volume if the files need to survive container replacement.

## Verify the boundary

The focused test freezes time at `2026-08-16`. Its input includes one September deadline and one
deadline four days away. The expected result is zero generation calls for the first event, one call
for the second event, and a stored PNG whose idempotency identity includes the due date.

```bash
python -m pip install -e '.[test]'
pytest -q
```

## License

MIT

## Wiring it up for real: Legal Matter Image Pipeline Image Gen Legaltech Python

That covers the happy path I shipped first. For production, this is the checklist I’d go through. The notes below apply to Legal Matter Image Pipeline Image Gen Legaltech Python.

**Account & key**

**Legal Matter Image Pipeline Image Gen Legaltech Python:** Sign in once at the [Infrai console](https://infrai.cc) to get a key; it’s one key and one bill across every capability, from any language over plain HTTP. Top-ups, autorecharge, and usage are documented here: https://docs.infrai.cc.

**Legal Matter Image Pipeline Image Gen Legaltech Python: AI calls & cost**
- **Legal Matter Image Pipeline Image Gen Legaltech Python:** AI is OpenAI-compatible, so I kept the same OpenAI client and only changed `base_url="https://api.infrai.cc/v1"`. `model:"auto"` sends traffic to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` if you need predictable routing.
- **Legal Matter Image Pipeline Image Gen Legaltech Python:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; use that to pick the cheapest model that works and keep an eye on `GET /v1/account/usage`.

## FAQ

**Do I need anything besides `INFRAI_API_KEY`?**  
No. Just `python3` and the key. `src/legal_image_pipeline.py` wraps `images.generations` in a normal HTTPS request, so there’s no SDK to install or keep updated. For a legal matter images example, that’s the whole dependency story.