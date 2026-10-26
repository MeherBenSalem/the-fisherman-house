#!/usr/bin/env bash
# Upgrade test: a 1.20.1 Fabric world made with The Fisherman House 1.1.0 (a 1.x house, half of it generated) is opened
# with the 2.0 jar from releases/. Real server, real loader, game on 25567 and RCON on 25577.
#   tools/qa/migration.sh <1.1.0 jar>
# 1.1.0 can be built from the commit before 2.0 (git worktree add <dir> fe82809; cd <dir>/1.20.1; ./gradlew :fabric:build).
set -uo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OLD_JAR=$(readlink -f "$1")
LOGS=${QA_LOGS:-/tmp/fc-qa}
dir="$LOGS/migration"
JDK=${JDK17:-$(ls -d /opt/jdks/jdk-17* /usr/lib/jvm/java-17-openjdk-amd64 2>/dev/null | head -1)}
prop() { grep "^$1=" "$ROOT/1.20.1/gradle.properties" | cut -d= -f2; }
NEW_JAR="$ROOT/releases/fisherman_house-fabric-1.20.1-$(prop version).jar"
rcon() { python3 "$ROOT/tools/qa/rcon.py" --port 25577 "$@"; }

start() {
  rm -f "$dir/server.log"
  (cd "$dir" && { nohup "$JDK/bin/java" -Xmx3G -jar server.jar nogui > server.log 2>&1 & echo $! > server.pid; })
  for _ in $(seq 1 240); do grep -q 'Done (' "$dir/server.log" 2>/dev/null && return 0; sleep 5; done
  echo "server did not start"; tail -n 30 "$dir/server.log"; exit 1
}
stop() {
  rcon stop > /dev/null 2>&1 || true
  pid=$(cat "$dir/server.pid")
  for _ in $(seq 1 60); do kill -0 "$pid" 2>/dev/null || return 0; sleep 2; done
  kill "$pid"
}
fail=0
check() { if [ "$2" = 0 ]; then echo "PASS $1"; else echo "FAIL $1"; fail=1; fi; }

rm -rf "$dir"; mkdir -p "$dir/mods"
installer=$(curl -fsSL https://maven.fabricmc.net/net/fabricmc/fabric-installer/maven-metadata.xml | grep -o '<release>[^<]*' | cut -d'>' -f2)
curl -fsSL -o "$dir/server.jar" "https://meta.fabricmc.net/v2/versions/loader/1.20.1/$(prop fabric_loader_version)/$installer/server/jar"
api=$(prop fabric_version)
curl -fsSL -o "$dir/mods/fabric-api.jar" "https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/$api/fabric-api-$api.jar"
echo 'eula=true' > "$dir/eula.txt"
printf 'enable-rcon=true\nrcon.port=25577\nrcon.password=qa\nonline-mode=false\nserver-port=25567\nlevel-name=old\nlevel-seed=1928374655\nmax-tick-time=-1\nview-distance=6\nspawn-monsters=false\n' > "$dir/server.properties"

# 1. 1.1.0: find a house and generate only the chunks on one side of its middle.
cp "$OLD_JAR" "$dir/mods/"
start
out=$(rcon "locate structure fisherman_house:fisherman_house")
echo "1.1.0: $out"
x=$(echo "$out" | sed -n 's/.*\[\(-\?[0-9]*\), ~, \(-\?[0-9]*\)\].*/\1/p'); z=$(echo "$out" | sed -n 's/.*\[\(-\?[0-9]*\), ~, \(-\?[0-9]*\)\].*/\2/p')
[ -n "$x" ] || { echo "FAIL 1.1.0 house not located"; stop; exit 1; }
rcon "forceload add $((x - 48)) $((z - 48)) $((x - 1)) $((z + 48))" > /dev/null
sleep 30
rcon "forceload remove all" "save-all flush" > /dev/null
before=$(rcon "execute if entity @e[type=minecraft:villager,name=Saylor,x=$((x - 48)),y=-64,z=$((z - 48)),dx=96,dy=384,dz=96]" | tr -d '\n')
echo "1.1.0 half-generated, Saylor generated: $before"
stop

# 2. The 2.0 jar on the same world.
rm "$dir/mods/$(basename "$OLD_JAR")"; cp "$NEW_JAR" "$dir/mods/"
start
grep -qE 'Found [0-9]+ mods|Loading [0-9]+ mods' "$dir/server.log"; check "2.0 loads the 1.1.0 world" $?
# 2.0 places houses closer together, so /locate may now find a newer one: the old house is checked where it was.
rcon "forceload add $((x - 48)) $((z - 48)) $((x + 48)) $((z + 48))" > /dev/null
sleep 30
info=$(rcon "fishermanscoast inspect $x 64 $z")
echo "2.0 inspect: $info"
echo "$info" | grep -q "id=fisherman_house "; check "the 1.x house is still there, now finished" $?
! echo "$info" | grep -q "containers=- "; check "the finished house has its barrels" $?
rcon "forceload remove all" > /dev/null
errors=$(grep -E '/(ERROR|FATAL)\]|Exception' "$dir/server.log" | grep -v 'Narrator' || true)
[ -z "$errors" ]; check "no errors in the 2.0 log" $?
[ -z "$errors" ] || echo "$errors" | head -5
stop
exit $fail
