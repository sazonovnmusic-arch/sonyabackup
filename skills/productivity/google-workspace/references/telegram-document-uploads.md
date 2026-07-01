# Telegram Document Upload Paths

## Problem

When a user uploads a file via Telegram **as a document** (not photo), Hermes saves it to a cache directory. The path typically looks like:

```
/root/.hermes/cache/documents/doc_<hash>_<filename>
```

The original filename is preserved in the suffix after the hash.

## Common pitfall

The agent may try to read the file from a generic path or expect the file at the current working directory. Always use the **exact path** from the message metadata.

## Pattern to follow

1. When a document upload is detected, note the `saved_at` path from the metadata.
2. Copy the file to a known location (e.g. `/root/client_secret.json`) before running setup scripts, or reference it with absolute path.
3. Do NOT rely on relative paths when calling scripts from different working directories — scripts may resolve paths differently.

## Example from session

```
/root/.hermes/cache/documents/doc_786e6604dbcd_client_secret_915818886720_...json
```

Copied to `/root/client_secret.json` before running `setup.py --client-secret`.