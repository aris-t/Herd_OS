#!/bin/bash
# Switch to AP mode for 120 seconds, then return to client

AP_UUID="54fa7950-badd-4fa4-a75e-9710c2737fb3"
CLIENT_UUID="8371517c-1619-467e-b862-53d255f3e6a5"
IFACE="wlan0"

echo "[INFO] Bringing up AP profile..."
#sudo systemctl stop dnsmasq
#sudo systemctl disable dnsmasq
sudo nmcli connection up uuid "$AP_UUID" ifname "$IFACE"

echo "[INFO] Waiting 120 seconds in AP mode..."
sleep 120

echo "[INFO] Switching back to client profile..."
sudo nmcli connection up uuid "$CLIENT_UUID" ifname "$IFACE"
#sudo systemctl start dnsmasq

echo "[INFO] Done."
