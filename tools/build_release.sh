#!/usr/bin/env bash
# Builds every workspace with its own JDK and copies the release jars into releases/:
#   tools/build_release.sh [workspace...]
# JDKs are looked up in /opt/jdks (jdk-17*, jdk-21*, jdk-25*) and /usr/lib/jvm; override with JDK17, JDK21, JDK25.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
find_jdk() { ls -d "/opt/jdks/jdk-$1"* "/usr/lib/jvm/java-$1-openjdk-amd64" 2>/dev/null | head -1 || true; }
JDK17=${JDK17:-$(find_jdk 17)}; JDK21=${JDK21:-$(find_jdk 21)}; JDK25=${JDK25:-$(find_jdk 25)}
mkdir -p "$ROOT/releases"
for ws in ${*:-1.20.1 1.21.1 26.1.2 26.2 26.3}; do
  case $ws in 1.20.1) jdk=$JDK17 ;; 1.21.1) jdk=$JDK21 ;; *) jdk=$JDK25 ;; esac
  version=$(grep '^version=' "$ROOT/$ws/gradle.properties" | cut -d= -f2)
  echo "== $ws with $jdk"
  (cd "$ROOT/$ws" && JAVA_HOME=$jdk ./gradlew clean build --no-daemon -q)
  for jar in "$ROOT/$ws"/{fabric,forge,neoforge}/build/libs/fisherman_house-*-"$version".jar; do
    [ -f "$jar" ] || continue
    cp "$jar" "$ROOT/releases/"
    echo "   $(basename "$jar")"
  done
done
