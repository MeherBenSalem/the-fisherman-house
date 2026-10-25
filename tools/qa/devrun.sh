#!/usr/bin/env bash
# Start or stop dev servers/clients for QA under Xvfb with software rendering.
#   tools/qa/devrun.sh prepare-server <workspace> <loader> [level-name] [level-type] [seed]
#     writes eula.txt and a server.properties with RCON on 25575 (password qa), offline mode and the given world
#     (default: world "qa", minecraft:normal, seed 1928374655); the world folder is deleted and the mod's config is
#     replaced by a short one with fast Crab Pots (5 s), which the mod must complete with its defaults and comments.
#   tools/qa/devrun.sh start-server <workspace> <loader>
#   tools/qa/devrun.sh start-client <workspace> <loader>
#   tools/qa/devrun.sh stop-client | stop-server [<workspace>]
# Logs go to $QA_LOGS (default /tmp/fc-qa).
set -u
LOGS=${QA_LOGS:-/tmp/fc-qa}
mkdir -p "$LOGS"
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
# Gradle runs on the workspace's Java: 17 for 1.20.1, 21 for 1.21.1, 25 for 26.x (override with QA_JAVA_HOME).
case "${2:-}" in
  1.20.1) default_java=$(ls -d /usr/lib/jvm/java-17-openjdk-amd64 /opt/jdks/jdk-17* 2>/dev/null | head -1) ;;
  1.21.1) default_java=$(ls -d /usr/lib/jvm/java-21-openjdk-amd64 /opt/jdks/jdk-21* 2>/dev/null | head -1) ;;
  *) default_java=$(ls -d /usr/lib/jvm/java-25-openjdk-amd64 /opt/jdks/jdk-25* 2>/dev/null | head -1) ;;
esac
JAVA_HOME=${QA_JAVA_HOME:-$default_java}
export JAVA_HOME
case "$1" in
  prepare-server)
    dir="$ROOT/$2/$3/runs/server"
    level=${4:-qa}
    mkdir -p "$dir"
    rm -rf "${dir:?}/$level"
    mkdir -p "$dir/config"
    printf '{"crab_pot": {"min_seconds": 5, "max_seconds": 5}}\n' > "$dir/config/fisherman_house.json"
    echo 'eula=true' > "$dir/eula.txt"
    cat > "$dir/server.properties" <<PROPS
enable-rcon=true
rcon.port=25575
rcon.password=qa
broadcast-rcon-to-ops=false
online-mode=false
level-name=$level
level-type=${5:-minecraft\:normal}
level-seed=${6:-1928374655}
spawn-protection=0
max-tick-time=-1
view-distance=8
simulation-distance=6
difficulty=normal
spawn-monsters=false
gamemode=creative
white-list=false
enforce-whitelist=false
PROPS
    if [ "$2" = 1.20.1 ] && [ "$3" = forge ]; then
      # A Forge 1.20.1 dev server otherwise tries to advertise itself to the LAN and fails in the sandbox.
      mkdir -p "$dir/defaultconfigs"
      printf '[server]\n\tadvertiseDedicatedServerToLan = false\n' > "$dir/defaultconfigs/forge-server.toml"
    fi
    ;;
  start-server)
    cd "$ROOT/$2" && nohup ./gradlew ":$3:runServer" --no-daemon > "$LOGS/$3-server.log" 2>&1 &
    ;;
  start-client)
    # Skip the first-launch screens (accessibility onboarding, multiplayer warning) and pausing when unfocused.
    opts="$ROOT/$2/$3/runs/client/options.txt"
    if [ ! -f "$opts" ]; then
      mkdir -p "$(dirname "$opts")"
      printf 'onboardAccessibility:false\nskipMultiplayerWarning:true\njoinedFirstServer:true\ntutorialStep:none\npauseOnLostFocus:false\nsoundCategory_master:0.0\nrenderDistance:8\n' > "$opts"
    fi
    # 26.3+ windows through SDL3, which only finds a usable visual on Xvfb through EGL.
    export DISPLAY=${DISPLAY:-:1} LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe SDL_VIDEO_FORCE_EGL=1 ${QA_CLIENT_ENV:-}
    cd "$ROOT/$2" && nohup ./gradlew ":$3:runQaClient" --no-daemon > "$LOGS/$3-client.log" 2>&1 &
    ;;
  stop-client|stop-server)
    # Only java processes are considered, so this never matches the calling shell.
    want=$([ "$1" = stop-client ] && echo 'KnotClient|clientQaClient|runQaClient|--quickPlayMultiplayer' || echo 'KnotServer|runServer|forgeserver|serverData|neoforgeserver')
    for pid in $(pgrep -x java); do
      cmd=$(tr '\0' ' ' < "/proc/$pid/cmdline")
      if echo "$cmd" | grep -qE "$want" && { [ -z "${2:-}" ] || echo "$cmd $(readlink "/proc/$pid/cwd")" | grep -q "/$2/"; }; then kill "$pid"; fi
    done
    ;;
esac
