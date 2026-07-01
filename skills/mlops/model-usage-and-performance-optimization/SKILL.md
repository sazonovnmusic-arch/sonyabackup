---
name: model-usage-and-performance-optimization
description: "Strategies for balancing model cost, context usage, and performance across different providers (Ollama Cloud, OpenRouter, etc.)."
version: 1.0.0
author: Hermes
---

# Model Usage and Performance Optimization

This skill provides guidance on selecting models based on their role (orchestrator vs. specialist) and managing resource consumption in cloud-based providers.

## Orchestration Strategy: Light vs. Heavy Models

### The Orchestrator Role
The orchestrator (main chat model) manages the conversation history, calls tools, and plans tasks. 
- **Light Models (e.g., Gemini Flash):** Usually faster and cheaper. However, they can have higher "session usage" if they carry large contexts or make frequent redundant tool calls.
- **Heavy Models (e.g., Kimiko, Claude Opus):** More expensive per token but often more efficient at following complex instructions in a single turn, which can lead to fewer iterations and lower overall usage in some environments (like Ollama Cloud).

**Decision Rule:** If a light model's "session usage" percentage grows 5-10x faster than a heavy model for the same tasks, revert to the heavy model as the orchestrator.

## Provider Quirks

### Ollama Cloud
- **Context Overhead:** Session usage counts the volume of data processed. Models with larger context windows (like Gemini Flash) may trigger higher usage billing if not carefully managed with context compression.
- **Vision Limitations:** `gemini-3-flash-preview` on Ollama Cloud may return a 400 error (`Invalid content part type: image_url`) when processing images through standard vision tools. Fallback to a different model or provider (e.g., Gemini via Google API directly) if vision is critical.

## Model Comparisons

- See `references/model-comparison-kimi-k2.6-vs-deepseek-v4-pro.md` for a detailed spec and benchmark comparison between Kimi K2.6 and DeepSeek V4 Pro (both on Ollama Cloud). Useful when deciding which model to assign to a profile.

## Evaluating Promotional / Free-Tier Models

- See `references/promotional-model-evaluation-openmodel.md` for a real-world example: DeepSeek V4 Flash offered free on OpenModel gateway, including observed specs, latency, and a reusable checklist for vetting promotional offers before routing production traffic.
- General rule: always verify RPM limits, output caps, TTFT penalty, and post-promo pricing before switching a profile to a free model.

## Optimization Techniques
- **Context Compression:** Use `/compress` to summarize history and reduce the token load on the orchestrator.
- **Delegation:** Use `delegate_task` to send isolated, low-context subtasks to specialized models, keeping the main orchestrator's history clean.

## Pitfall: Per-Million Pricing ≠ Real Session Cost

A common trap: judging models only by their published price per million tokens. In practice, some "cheap" models burn through context far faster than "expensive" ones.

**Real example (Ollama Cloud):**
- `gemini-3-flash`: advertised cheap per-million
- `kimi-k2.6:cloud`: higher per-million price
- **Observed result:** gemini-3-flash produced **5-10× higher session usage** in real workflows, making it more expensive overall despite the lower rate card.

**Rule:** When a user says "this model eats tokens" or "real usage is higher than expected," always check the actual session-usage percentage in Hermes logs, not just the rate card. Prefer the model with lower real-world burn even if its per-million price is higher.

**How to check:**
```bash
# Look at recent agent logs for "session usage" or context compression events
tail -50 ~/.hermes/logs/agent.log | grep -i "usage\|compression\|tokens"
```