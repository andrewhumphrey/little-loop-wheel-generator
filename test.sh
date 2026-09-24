#!/bin/bash
set -euo pipefail

URL='https://littleloop.ajh.is'
FUNCTION_NAME="little-loop-wheel-generator"
REGION="ap-southeast-2"
TMP_DIR="$(mktemp -d)"
CONFIG_FILE="${TMP_DIR}/config.json"
ORIGINAL_ENV_FILE="${TMP_DIR}/original-env.json"
TEST_ENV_FILE="${TMP_DIR}/test-env.json"
PAYLOAD_FILE="${TMP_DIR}/event.json"
RESPONSE_FILE="${TMP_DIR}/response.json"
#trap 'rm -rf "${TMP_DIR}"' EXIT

echo "JSON"
curl -u littleloop:KilkennyInTheRedCan -i -H 'Accept: application/json' "${URL}"
echo
echo "HTML"
curl -u littleloop:KilkennyInTheRedCan -i "${URL}"
echo

echo "Scheduled event - backing up environment"
#!/usr/bin/env bash
set -euo pipefail


restore_environment() {
  echo "Restoring original environment variables..."
  aws lambda update-function-configuration \
    --function-name "${FUNCTION_NAME}" \
    --region "${REGION}" \
    --environment "file://${ORIGINAL_ENV_FILE}" >/dev/null

  aws lambda wait function-updated \
    --function-name "${FUNCTION_NAME}" \
    --region "${REGION}"

  echo "Original environment variables restored."
}

cleanup() {
  script_status=$?
  trap - EXIT

  if [[ -f "${ORIGINAL_ENV_FILE}" ]]; then
    restore_environment || echo "WARNING: Could not restore the original environment."
  fi

  #rm -rf "${TMP_DIR}"
  echo "NOT CLEANING UP ${TMP_DIR}"
  exit "${script_status}"
}
trap cleanup EXIT

aws lambda get-function-configuration \
  --function-name "${FUNCTION_NAME}" \
  --region "${REGION}" > "${CONFIG_FILE}"

# AWS CLI update-function-configuration expects {"Variables": {...}}.
jq '{Variables: (.Environment.Variables // {})}' \
  "${CONFIG_FILE}" > "${ORIGINAL_ENV_FILE}"

jq '.Variables.EMAIL_RECIPIENTS = "andrew@ajh.is"' \
  "${ORIGINAL_ENV_FILE}" > "${TEST_ENV_FILE}"

cat > "${PAYLOAD_FILE}" <<'JSON'
{
  "version": "0",
  "id": "example-event-id",
  "detail-type": "Scheduled Event",
  "source": "aws.events",
  "account": "748390101883",
  "time": "2026-09-24T00:00:00Z",
  "region": "ap-southeast-2",
  "resources": [
    "arn:aws:events:ap-southeast-2:748390101883:rule/example-schedule"
  ],
  "detail": {}
}
JSON

aws lambda update-function-configuration \
  --function-name "${FUNCTION_NAME}" \
  --region "${REGION}" \
  --environment "file://${TEST_ENV_FILE}" >/dev/null

aws lambda wait function-updated \
  --function-name "${FUNCTION_NAME}" \
  --region "${REGION}"

aws lambda invoke \
  --function-name "${FUNCTION_NAME}" \
  --region "${REGION}" \
  --cli-binary-format raw-in-base64-out \
  --payload "file://${PAYLOAD_FILE}" \
  "${RESPONSE_FILE}"

echo "Lambda response:"
cat "${RESPONSE_FILE}"
echo
