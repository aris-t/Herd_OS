#!/bin/bash
# /usr/local/bin/wifi-auto-fallback.sh
# Self-elevate
if [ "$EUID" -ne 0 ]; then exec sudo "$0" "$@"; fi

CLIENT_UUID="8371517c-1619-467e-b862-53d255f3e6a5"   # client profile
AP_UUID="63106ee2-2220-4bd6-a436-eda41654a495"       # AP profile
IFACE="wlan0"
KNOWN_SSIDS=("Infrastructure_1" "Infrastructure_2" "Infrastructure_3" "SABRPI" "404-Network-Not-Found_5G")

scan_for_known() {
  nmcli dev wifi rescan >/dev/null 2>&1
  local visible
  visible=$(nmcli -t -f SSID dev wifi list | sort -u)
  for s in "${KNOWN_SSIDS[@]}"; do
    grep -Fxq "$s" <<<"$visible" && { echo "$s"; return 0; }
  done
  return 1
}

active_uuid() {
  nmcli -t -f DEVICE,UUID connection show --active | awk -F: -v d="$IFACE" '$1==d{print $2; exit}'
}

ensure_client() {
  local au; au=$(active_uuid)
  [[ "$au" == "$CLIENT_UUID" ]] && return 0
  nmcli con up uuid "$CLIENT_UUID" ifname "$IFACE" >/dev/null 2>&1
}

ensure_ap() {
  local au; au=$(active_uuid)
  [[ "$au" == "$AP_UUID" ]] && return 0
  nmcli con up uuid "$AP_UUID" ifname "$IFACE" >/dev/null 2>&1
}

COOLDOWN=10  # seconds between state changes
last_switch=0

echo "[wifi-auto] started"
while true; do
  now=$(date +%s)
  if (( now - last_switch < COOLDOWN )); then
    sleep 1; continue
  fi

  if scan_for_known >/dev/null; then
    ensure_client && last_switch=$(date +%s)
  else
    ensure_ap && last_switch=$(date +%s)
  fi

  sleep 15
done
