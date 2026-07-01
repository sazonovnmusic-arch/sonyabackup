# Google Calendar: Recurring Events

## Problem

Recurring events in Google Calendar have a **master event** (the series) and **individual instances**. When you delete one instance via `calendar delete INSTANCE_ID`, only that single occurrence is removed. The master event continues generating new instances for future dates.

## Why it matters

A bulk-delete loop that naïvely iterates over visible instances will **never finish** — new instances keep appearing, or the same recurring series keeps spawning replacements.

## How to clean up properly

| Approach | When to use |
|----------|-------------|
| **Delete the master series in the UI** | User wants to wipe everything. Go to Google Calendar web/app, open the series, choose "Delete all upcoming" or "Delete entire series". |
| **Stop iterating visible instances** | If code/API shows endless events after a batch delete, it's recurring. Stop and warn the user. |
| **Use `recurringEventId` from API** | If fetching via API, check `recurringEventId` field. Deleting the master ID removes the whole series (requires write scope). |

## Red flags

- After deleting N events, `calendar list` still returns events for the same dates.
- Event IDs share a common base prefix with date suffixes (e.g. `abc_20260623T060000Z`, `abc_20260624T060000Z`).

## Session note

In practice, tell the user: *"These are recurring events. I can only delete single copies; to wipe the series, open Google Calendar, find the event, and choose 'Delete all upcoming' or 'Delete entire series'."*