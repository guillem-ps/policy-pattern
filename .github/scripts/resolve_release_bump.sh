#!/usr/bin/env bash
set -euo pipefail

matches=()
for label in "$@"; do
  case "$label" in
    release:major|release:minor|release:patch)
      case " ${matches[*]} " in
        *" $label "*) ;;
        *) matches+=("$label") ;;
      esac
      ;;
  esac
done

if [ "${#matches[@]}" -gt 1 ]; then
  printf 'Error: conflicting release labels: %s\n' "${matches[*]}" >&2
  exit 1
fi

if [ "${#matches[@]}" -eq 1 ]; then
  printf '%s\n' "${matches[0]#release:}"
fi
