#!/usr/bin/env bash

set -euo pipefail

nonce="$(uuidgen)"
configured_overrides="$(sed -n 's/^parameter_overrides = "\(.*\)"$/\1/p' samconfig.toml)"
sam_command="${SAM_COMMAND:-sam}"

if [[ -z "$configured_overrides" ]]; then
  echo "Could not read parameter_overrides from samconfig.toml." >&2
  exit 1
fi

"$sam_command" build

"$sam_command" deploy --parameter-overrides "$configured_overrides DeploymentNonce=\"$nonce\"" "$@"
