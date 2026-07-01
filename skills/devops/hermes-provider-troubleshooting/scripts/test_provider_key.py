#!/usr/bin/env python3
"""
Test a Hermes LLM provider API key for both metadata access and inference.
Usage:
  python3 test_provider_key.py --provider ollama-cloud --key "sk-..." --model "kimi-k2.6"
"""
import argparse
import json
import sys
import urllib.error
import urllib.request

PROVIDERS = {
    "ollama-cloud": {"base": "https://ollama.com/v1", "header": "Authorization"},
    "openrouter": {"base": "https://openrouter.ai/api/v1", "header": "Authorization"},
    "google": {"base": "https://generativelanguage.googleapis.com/v1beta", "header": "x-goog-api-key"},
}


def test_list(base_url: str, key: str, header_name: str) -> bool:
    req = urllib.request.Request(f"{base_url}/models")
    req.add_header(header_name, f"Bearer {key}" if header_name == "Authorization" else key)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            models = [m["id"] for m in data.get("data", [])]
            print(f"  Model list OK ({len(models)} models)")
            return True
    except urllib.error.HTTPError as e:
        print(f"  Model list FAILED: HTTP {e.code} {e.reason}")
        return False


def test_inference(base_url: str, key: str, model: str, header_name: str) -> bool:
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 5,
    }).encode()
    req = urllib.request.Request(f"{base_url}/chat/completions", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    req.add_header(header_name, f"Bearer {key}" if header_name == "Authorization" else key)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            print(f"  Inference OK (HTTP {resp.status})")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print(f"  Inference FAILED: HTTP {e.code} {e.reason}")
        print(f"    Body: {body}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Validate LLM provider API key")
    parser.add_argument("--provider", required=True, choices=list(PROVIDERS.keys()) + ["custom"])
    parser.add_argument("--key", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", default=None)
    args = parser.parse_args()

    if args.provider == "custom":
        if not args.base_url:
            print("--base-url required for custom provider")
            sys.exit(1)
        base = args.base_url.rstrip("/")
        header = "Authorization"
    else:
        base = PROVIDERS[args.provider]["base"]
        header = PROVIDERS[args.provider]["header"]

    print(f"Testing {args.provider} (model: {args.model})")
    ok_list = test_list(base, args.key, header)
    ok_inf = test_inference(base, args.key, args.model, header)

    if ok_list and ok_inf:
        print("\n✅ Key is FULLY functional (metadata + inference)")
        sys.exit(0)
    elif ok_list and not ok_inf:
        print("\n⚠️  Key works for metadata but NOT inference — check billing/plan/permissions")
        sys.exit(2)
    else:
        print("\n❌ Key is invalid or expired")
        sys.exit(1)


if __name__ == "__main__":
    main()
