#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
JAVA="$ROOT/runtime/bin/java"
[ -x "$JAVA" ] || JAVA=java
CP="$ROOT/classes:$ROOT/lib/*:$ROOT/jars/*:$ROOT"
exec "$JAVA" -cp "$CP" groovy.ui.GroovyMain "$ROOT/$1"
