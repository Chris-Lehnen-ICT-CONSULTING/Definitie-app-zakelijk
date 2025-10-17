#!/bin/bash
set -euo pipefail

# Load local secrets without committing them
if [[ -f "${HOME}/.config/mcp/perplexity.env" ]]; then
	# shellcheck disable=SC1090
	source "${HOME}/.config/mcp/perplexity.env"
fi

if [[ -z ${PERPLEXITY_API_KEY-} ]]; then
	echo "PERPLEXITY_API_KEY is not set. Create ${HOME}/.config/mcp/perplexity.env with:"
	echo "export PERPLEXITY_API_KEY=your_key_here"
	exit 1
fi

# Adjust this to your installed server binary or npx command
exec perplexity-mcp "$@"
