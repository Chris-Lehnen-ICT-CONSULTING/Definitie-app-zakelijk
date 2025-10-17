#!/bin/bash
set -euo pipefail

# Load local secrets
if [[ -f "${HOME}/.config/mcp/context7.env" ]]; then
	# shellcheck disable=SC1090
	source "${HOME}/.config/mcp/context7.env"
fi

if [[ -z ${CONTEXT7_API_KEY-} ]]; then
	echo "CONTEXT7_API_KEY is not set. Create ${HOME}/.config/mcp/context7.env with:"
	echo "export CONTEXT7_API_KEY=your_key_here"
	echo "export CONTEXT7_BASE_URL=https://api.context7.example"
	exit 1
fi

# Adjust this to your installed server binary or npx command
exec context7-mcp "$@"
