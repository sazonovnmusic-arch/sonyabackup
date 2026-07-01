#!/bin/bash
# Hermes YouTube Gateway Launcher
# Sources global env + profile env before running gateway

export HOME=/root
export USER=root

# Load global .env
if [ -f "$HOME/.hermes/.env" ]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line%%#*}"
        line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [[ -n "$line" && "$line" == *=* ]]; then
            key="${line%%=*}"
            val="${line#*=}"
            if [[ -n "${key// }" && "$key" != *"#"* ]]; then
                export "$key=$val"
            fi
        fi
    done < "$HOME/.hermes/.env"
fi

# Load profile .env (overrides global where needed)
if [ -f "$HOME/.hermes/profiles/youtube/.env" ]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line%%#*}"
        line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [[ -n "$line" && "$line" == *=* ]]; then
            key="${line%%=*}"
            val="${line#*=}"
            if [[ -n "${key// }" && "$key" != *"#"* ]]; then
                export "$key=$val"
            fi
        fi
    done < "$HOME/.hermes/profiles/youtube/.env"
fi

# Run gateway
cd /root
exec /usr/local/lib/hermes-agent/venv/bin/hermes -p youtube gateway run
