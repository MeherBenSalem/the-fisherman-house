#!/usr/bin/env bash
# Smoke-tests a release jar from releases/ on a real (production) server: vanilla Minecraft with the real loader
# installed by its installer, the remapped jar (plus Fabric API on Fabric), RCON on 25576 and the game on 25566, so it
# can run beside a dev server. The server never pauses when empty (newer versions stop ticking after 60 s without
# players, and the checks run without one).
#   tools/qa/prodserver.sh setup <workspace> <loader>   # download and install into $QA_LOGS/prod/<ws>-<loader>
#   tools/qa/prodserver.sh start <workspace> <loader>
#   tools/qa/prodserver.sh check <workspace> <loader>   # coast_checks.py (server checks) against it
#   tools/qa/prodserver.sh stop  <workspace> <loader>   # "stop" over RCON, then the server's own PID
#   tools/qa/prodserver.sh run   <workspace> <loader>   # setup, start, check, stop
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
LOGS=${QA_LOGS:-/tmp/fc-qa}
cmd=$1; ws=$2; loader=$3
dir="$LOGS/prod/$ws-$loader"
prop() { grep "^$1=" "$ROOT/$ws/gradle.properties" | cut -d= -f2; }
find_jdk() { ls -d "/opt/jdks/jdk-$1"* "/usr/lib/jvm/java-$1-openjdk-amd64" 2>/dev/null | head -1 || true; }
case $ws in 1.20.1) jdk=${JDK17:-$(find_jdk 17)} ;; 1.21.1) jdk=${JDK21:-$(find_jdk 21)} ;; *) jdk=${JDK25:-$(find_jdk 25)} ;; esac
mc=$(prop minecraft_version); version=$(prop version)
jar="$ROOT/releases/fisherman_house-$loader-$mc-$version.jar"
fetch() { curl -fsSL --retry 4 -o "$2" "$1"; }

setup() {
  [ -f "$jar" ] || { echo "missing $jar (run tools/build_release.sh)"; exit 1; }
  rm -rf "$dir"; mkdir -p "$dir/mods" "$dir/config"
  case $loader in
    fabric)
      installer=$(curl -fsSL https://maven.fabricmc.net/net/fabricmc/fabric-installer/maven-metadata.xml | grep -o '<release>[^<]*' | cut -d'>' -f2)
      fetch "https://meta.fabricmc.net/v2/versions/loader/$mc/$(prop fabric_loader_version)/$installer/server/jar" "$dir/server.jar"
      api=$(prop fabric_version)
      fetch "https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/$api/fabric-api-$api.jar" "$dir/mods/fabric-api-$api.jar" ;;
    forge)
      v="$mc-$(prop forge_version)"
      fetch "https://maven.minecraftforge.net/net/minecraftforge/forge/$v/forge-$v-installer.jar" "$dir/installer.jar"
      (cd "$dir" && "$jdk/bin/java" -jar installer.jar --installServer > install.log 2>&1) ;;
    neoforge)
      v=$(prop neoforge_version)
      fetch "https://maven.neoforged.net/releases/net/neoforged/neoforge/$v/neoforge-$v-installer.jar" "$dir/installer.jar"
      (cd "$dir" && "$jdk/bin/java" -jar installer.jar --installServer > install.log 2>&1) ;;
  esac
  cp "$jar" "$dir/mods/"
  echo 'eula=true' > "$dir/eula.txt"
  printf '{"crab_pot": {"min_seconds": 5, "max_seconds": 5}}\n' > "$dir/config/fisherman_house.json"
  cat > "$dir/server.properties" <<PROPS
enable-rcon=true
rcon.port=25576
rcon.password=qa
broadcast-rcon-to-ops=false
online-mode=false
server-port=25566
level-name=prod
level-seed=1928374655
spawn-protection=0
max-tick-time=-1
view-distance=8
simulation-distance=6
difficulty=normal
spawn-monsters=false
pause-when-empty-seconds=-1
PROPS
  echo "set up $dir with $(basename "$jar")"
}

start() {
  cd "$dir"
  rm -f server.log
  if [ -f server.jar ]; then
    nohup "$jdk/bin/java" -Xmx3G -jar server.jar nogui > server.log 2>&1 &
  else
    echo '-Xmx3G' > user_jvm_args.txt
    PATH="$jdk/bin:$PATH" nohup bash ./run.sh nogui > server.log 2>&1 &
  fi
  echo $! > server.pid
  for _ in $(seq 1 240); do
    grep -q 'Done (' server.log 2>/dev/null && { echo "started $ws $loader"; return 0; }
    kill -0 "$(cat server.pid)" 2>/dev/null || break
    sleep 5
  done
  echo "server did not start: $dir/server.log"; tail -n 30 server.log; exit 1
}

check() {
  python3 "$ROOT/tools/qa/coast_checks.py" --port 25576 --log "$dir/server.log" --config "$dir/config/fisherman_house.json" \
    --minecraft "$mc"
}

stop() {
  python3 "$ROOT/tools/qa/rcon.py" --port 25576 stop > /dev/null 2>&1 || true
  [ -f "$dir/server.pid" ] || return 0
  pid=$(cat "$dir/server.pid")
  for _ in $(seq 1 30); do kill -0 "$pid" 2>/dev/null || return 0; sleep 2; done
  # run.sh starts java as its child: stop the child, then the script.
  for child in $(ps -o pid= --ppid "$pid" 2>/dev/null); do kill "$child" 2>/dev/null || true; done
  kill "$pid" 2>/dev/null || true
}

case $cmd in
  setup) setup ;;
  start) start ;;
  check) check ;;
  stop) stop ;;
  run) setup; start; status=0; check || status=$?; stop; exit $status ;;
  *) echo "unknown command $cmd"; exit 2 ;;
esac
