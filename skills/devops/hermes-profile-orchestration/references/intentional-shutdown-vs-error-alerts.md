# Intentional Shutdown vs Error Alerts in Multi-Profile Systems

## The Problem

In a multi-profile Hermes deployment where some profiles are intentionally kept offline (e.g., `coding` is powered down until needed), a server health monitor that treats ALL stopped services as failures generates false-positive alerts.

**Concrete scenario:**
- `hermes-gateway-coding.service` is in `failed` or `inactive` state intentionally — user shut it down to save RAM.
- Server watchdog cron (`server_monitor.py`) lists all 4 gateway statuses every day at 21:00.
- Output shows `🔴 hermes-gateway-coding: failed` and `🔴 hermes-gateway-traffic: failed`.
- This floods the user with unnecessary alerts, creating alert fatigue.

## Root Causes

1. **Monitoring script lacks intent-awareness.** `check_gateways()` iterates a hardcoded list:
   ```python
   services = [
       'hermes-gateway',
       'hermes-gateway-youtube',
       'hermes-gateway-coding',
       'hermes-gateway-traffic',
   ]
   ```
   Every service in the list is treated equally — no concept of "expected state."

2. **No differentiation between intentional shutdown and crash.** Systemd `failed` state can mean:
   - `systemctl stop` (intentional) → `inactive (dead)`
   - `kill -9` or crash → `failed`
   - Dependency failure → `failed`
   Script reports all identically.

3. **Cronjob stdout always delivered.** With `no_agent=true`, the script's entire stdout is sent verbatim every run, even when nothing is critically wrong.

## Solutions

### Option A: Filter by Expected State (Recommended)

Modify `check_gateways()` to skip services that are expected to be down:

```python
EXPECTED_ACTIVE = ['hermes-gateway', 'hermes-gateway-youtube']

def check_gateways():
    services = [
        'hermes-gateway',
        'hermes-gateway-youtube',
        'hermes-gateway-coding',
        'hermes-gateway-traffic',
    ]
    statuses = {}
    for svc in services:
        result = run(f'systemctl is-active {svc}.service 2>/dev/null')
        statuses[svc] = result.stdout.strip() if result else 'unknown'
    return statuses

def report_gateways(statuses):
    active = {k: v for k, v in statuses.items() if k in EXPECTED_ACTIVE}
    inactive = {k: v for k, v in statuses.items() if k not in EXPECTED_ACTIVE}
    
    lines = []
    for svc, st in active.items():
        emoji = "🟢" if st == 'active' else "🔴"
        lines.append(f"{emoji} {svc}: {st}")
    
    # Only report inactive services if they unexpectedly became ACTIVE
    # (waste of RAM) or if they're FAILED (was intentionally stopped but crashed)
    for svc, st in inactive.items():
        if st == 'failed':
            lines.append(f"⚠️ {svc}: {st} (unexpected — was intentionally down)")
        elif st == 'active':
            lines.append(f"💡 {svc}: {st} (unexpectedly running — wasting RAM)")
    
    return lines
```

### Option B: Suppress Healthy Reports

Add a silence threshold — only deliver output if there is a real anomaly:

```python
if all_ok and pct_used < 85 and mem.percent < 90 and not unexpected_failures:
    # Nothing to report — empty stdout = cronjob stays silent
    exit(0)
```

With `no_agent=true` cronjobs, empty stdout means **silent run** — no message is sent. The user sees nothing unless something truly needs attention.

### Option C: Per-Profile systemd State Tracking

Create a simple flag file to indicate intentional state:

```bash
# When intentionally stopping a profile
systemctl stop hermes-gateway-coding
touch /root/.hermes/profiles/coding/.intentionally_stopped

# When starting
systemctl start hermes-gateway-coding
rm -f /root/.hermes/profiles/coding/.intentionally_stopped
```

Monitor script checks flag before reporting `failed`:

```python
profile = svc.replace('hermes-gateway-', '').replace('hermes-gateway', 'default')
flag = Path(f'/root/.hermes/profiles/{profile}/.intentionally_stopped')
if st != 'active' and flag.exists():
    # Intentionally down — skip or report as "💤 sleeping"
    continue
```

## Prevention Checklist

- [ ] When adding a new profile, decide: is it 24/7 or on-demand?
- [ ] Update `EXPECTED_ACTIVE` list in `server_monitor.py` accordingly.
- [ ] Set `hermes-sleep` wrapper to create `.intentionally_stopped` flag.
- [ ] Set `hermes-wake` wrapper to remove flag.
- [ ] If using systemd auto-restart (`Restart=on-failure`), an intentionally stopped service may flip to `failed` then restart. Set `Restart=no` for on-demand profiles, or use `RestartForceExitStatus=` to exclude clean exits.

## Related

- `references/memory-saving-multi-profile.md` — wake/sleep pattern for RAM saving.
- `references/systemd-multi-profile-units.md` — unit file templates with Restart policies.
- `references/gateway-self-preservation-rule.md` — why agents must not restart their own gateway.
