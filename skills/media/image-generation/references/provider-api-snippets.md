# Provider API Snippets for Image Generation

## FAL.ai

### Img2img (FLUX Redux)
```bash
curl -X POST https://fal.run/fal-ai/flux-redux \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "data:image/jpeg;base64,...",
    "prompt": "style description",
    "strength": 0.65,
    "num_images": 1,
    "aspect_ratio": "9:16"
  }'
```

### Text-to-image (FLUX Pro)
```bash
curl -X POST https://fal.run/fal-ai/flux-pro \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "photo description",
    "num_images": 1,
    "aspect_ratio": "9:16"
  }'
```

## Replicate

### Img2img (FLUX Schnell)
```python
import requests, base64, time

with open('photo.jpg', 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()

headers = {
    'Authorization': 'Token r8_...',
    'Content-Type': 'application/json'
}

payload = {
    'version': 'black-forest-labs/flux-schnell',
    'input': {
        'image': f'data:image/jpeg;base64,{img_b64}',
        'prompt': 'style description',
        'strength': 0.7,
        'aspect_ratio': '9:16'
    }
}

r = requests.post('https://api.replicate.com/v1/predictions', headers=headers, json=payload)
data = r.json()
pred_id = data['id']

# Poll until done
while True:
    poll = requests.get(f'https://api.replicate.com/v1/predictions/{pred_id}', headers=headers)
    status = poll.json()['status']
    if status == 'succeeded':
        output_url = poll.json()['output'][0]
        break
    time.sleep(2)
```

## OpenAI (text-to-image only, NO img2img)

```bash
curl https://api.openai.com/v1/images/generations \
  -H "Authorization: Bearer $OPENAI_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "dall-e-3",
    "prompt": "photo description",
    "n": 1,
    "size": "1024x1536"
  }'
```

## Pollinations.ai (free, text-to-image only)

```bash
# Simple GET
curl "https://image.pollinations.ai/prompt/photo%20description?width=720&height=1280&seed=42&nologo=true" \
  -o result.png

# With POST (image ref unreliable)
curl -X POST https://image.pollinations.ai/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "photo description",
    "width": 720,
    "height": 1280,
    "seed": 42
  }'
```

## Error Quick Reference

| Status | Provider | Meaning | Fix |
|--------|----------|---------|-----|
| 403 | FAL | Balance exhausted | Top up at fal.ai/dashboard/billing |
| 401 | OpenAI | Invalid/expired key | Create new at platform.openai.com/api-keys |
| 401 | Replicate | Invalid token | Regenerate at replicate.com/account/api-tokens |
| 404 | FAL | Model not found | Check model name, try `flux-pro` or `flux-pro/v1.1` |
