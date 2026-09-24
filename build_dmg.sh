#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/build_silicon_dmg.sh" "$@"
