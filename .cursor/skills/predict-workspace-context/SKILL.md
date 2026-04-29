---
name: predict-workspace-context
description: Loads and maintains the Predict WebApp project context. Use when working in this final_test workspace, before code, document, UI, data-contract, or deployment changes, and after changes that affect durable project facts.
---

# Predict Workspace Context

## Required First Step

Before making changes in this workspace, read `AI_CONTEXT.md`.

Use it as the project routing document:

1. Read `AI_CONTEXT.md` for durable project facts, module boundaries, and the default documentation route.
2. Based on the task type, read the referenced files under `document/` or `document/interfaces/`.
3. Treat `promblem.md` as the source of truth for assignment constraints when task requirements touch prediction behavior, input/output format, rolling evaluation, or leakage rules.

## Maintenance Rule

After code, document, UI, data-contract, or deployment changes, decide whether any durable project facts changed.

If they did, update `AI_CONTEXT.md` in the same work session. Keep it concise:

- Store only stable facts, routing guidance, module boundaries, and collaboration conventions.
- Put detailed implementation notes in `document/` or `document/interfaces/`.
- Do not duplicate long specs from detailed documents.

## Important Current Facts

- The app is a Streamlit time-series prediction WebApp exposed at `/predict`.
- User uploads `.xlsx`; the first sheet must include `y` and may include `date`.
- The app must immediately output a one-step forecast `y_{N+1}` after upload.
- Rolling backtest uses chronological 80/20 split with strict one-step rolling prediction.
- Output `.xlsx` must include predicted `y`; include `date` when the input has `date`.
- Avoid data leakage: prediction must not use future values.
