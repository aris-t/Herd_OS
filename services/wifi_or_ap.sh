#!/usr/bin/env bash
set -euo pipefail

WLAN="wlan0"
AP_IP="10.0.0.1/24"
AP_GW="10.0.0.1"
CHECK_URL="http://connectivitycheck.gstatic.com/generate_204"
STATE_FILE="/run/wifi_portal.state"

start_client() {
  echo "-> Client mode"
  # Kill AP stack if running
  systemctl stop hostapd || true
  systemctl stop dnsmasq || true
  # Remove AP IP + iptables DNAT
  ip addr flush dev "$WLAN" || true
  ip link set "$WLAN" up || true
  # Clear HTTP DNAT (if present)
  iptables -t nat -C PREROUTING -i "$WLAN" -p tcp --dport 80 -j DNAT --to-destination ${AP_GW}:80 2>/dev/null && \
    iptables -t nat -D PREROUTING -i "$WLAN" -p tcp --dport 80 -j DNAT --to-destination ${AP_GW}:80 || true

  # NAT off is fine; leave MASQUERADE on eth0 if you use it elsewhere.

  # Start client stack
  rfkill unblock wifi || true
  systemctl restart wpa_supplicant@wlan0.service
  systemctl restart dhcpcd.service

  # Wait for IP + internet
  for _ in {1..20}; do
    sleep 1
    ip addr show "$WLAN" | grep -q "inet " || continue
    curl -m 2 -fsS "$CHECK_URL" >/dev/null && echo "CLIENT" > "$STATE_FILE" && return 0
  done

  echo "Client mode failed to get internet."
  return 1
}

start_ap() {
  echo "-> AP mode (captive portal)"
  # Stop client stack
  systemctl stop wpa_supplicant@wlan0.service || true

  # Set static IP and link up
  ip addr flush dev "$WLAN" || true
  ip link set "$WLAN" up || true
  ip addr add "$AP_IP" dev "$WLAN" || true

  # DNS/DHCP + AP
  systemctl restart dnsmasq
  systemctl restart hostapd

  # Force HTTP to portal
  iptables -t nat -C PREROUTING -i "$WLAN" -p tcp --dport 80 -j DNAT --to-destination ${AP_GW}:80 2>/dev/null || \
    iptables -t nat -A PREROUTING -i "$WLAN" -p tcp --dport 80 -j DNAT --to-destination ${AP_GW}:80

  # (Optional) enable internet egress for clients via eth0
  sysctl -w net.ipv4.ip_forward=1 >/dev/null
  # Keep your MASQUERADE rule from earlier if desired

  # Ensure web stack is up
  systemctl restart nginx
  systemctl restart fastapi

  echo "AP" > "$STATE_FILE"
}

is_connected() {
  curl -m 2 -fsS "$CHECK_URL" >/dev/null
}

loop() {
  # Try client first
  if start_client; then
    :
  else
    start_ap
  fi

  # Monitor and auto-switch
  while true; do
    sleep 10
    MODE="$(cat "$STATE_FILE" 2>/dev/null || echo UNKNOWN)"

    if [[ "$MODE" == "CLIENT" ]]; then
      # If client lost internet for ~30s, fall back to AP
      if ! is_connected; then
        sleep 20
        if ! is_connected; then
          start_ap
        fi
      fi
    else
      # In AP mode: periodically see if real internet is available on known APs
      # Quick scan for known SSIDs present
      if iw dev "$WLAN" scan 2>/dev/null | grep -qE "SSID: (LabWiFi|BarnAP)"; then
        # Try flipping to client; if success, it will stick
        start_client || true
      fi
    fi
  done
}

loop

