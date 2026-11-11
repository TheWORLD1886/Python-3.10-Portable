#!/usr/bin/env bash
# Install MetaTrader 5 (XM) + NTI EA on an Ubuntu 22.04/24.04 server via Wine, headless (Xvfb).
#
# STATUS: NOT TESTED end-to-end. Written from MetaQuotes' documented Wine procedure and
# MT5 command-line options. Run it on a fresh DEMO setup and check every step's output.
#
# Usage (as a normal user with sudo):
#   cp xm_demo.env.example ~/.nti/xm_demo.env && chmod 600 ~/.nti/xm_demo.env   # fill it in
#   bash install_mt5_xm.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
export WINEPREFIX="${WINEPREFIX:-$HOME/.mt5}"
export WINEDEBUG=-all
ENV_FILE="$HOME/.nti/xm_demo.env"

echo "[1/6] System packages (wine, xvfb)"
sudo dpkg --add-architecture i386
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y wine wine64 xvfb curl

echo "[2/6] MetaTrader 5 installer (official MetaQuotes URL; XM's own installer also works)"
mkdir -p "$HOME/.nti/dl"
curl -fL -o "$HOME/.nti/dl/mt5setup.exe" \
  https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe
xvfb-run -a sh -c "wineboot -i; wine '$HOME/.nti/dl/mt5setup.exe' /auto; wineserver -w"

MT5_DIR="$(dirname "$(find "$WINEPREFIX/drive_c" -iname terminal64.exe | head -1)")"
[ -n "$MT5_DIR" ] || { echo "terminal64.exe not found - installation failed"; exit 1; }
echo "MT5 installed at: $MT5_DIR"

echo "[3/6] Copy and compile the EA"
mkdir -p "$MT5_DIR/MQL5/Experts/NTI"
cp "$REPO_DIR/mql5/Experts/NTI_LiquiditySweep.mq5" "$MT5_DIR/MQL5/Experts/NTI/"
( cd "$MT5_DIR" && xvfb-run -a wine metaeditor64.exe \
    /compile:"MQL5\\Experts\\NTI\\NTI_LiquiditySweep.mq5" /log:"MQL5\\Experts\\NTI\\compile.log" ) || true
iconv -f UTF-16LE -t UTF-8 "$MT5_DIR/MQL5/Experts/NTI/compile.log" 2>/dev/null | tail -5 || true
[ -f "$MT5_DIR/MQL5/Experts/NTI/NTI_LiquiditySweep.ex5" ] || { echo "COMPILE FAILED - see compile.log"; exit 1; }

echo "[4/6] Startup config (credentials read from $ENV_FILE, never stored in git)"
[ -f "$ENV_FILE" ] || { echo "Missing $ENV_FILE (see xm_demo.env.example)"; exit 1; }
# shellcheck disable=SC1090
source "$ENV_FILE"
umask 077
cat > "$MT5_DIR/nti_startup.ini" <<EOF
[Common]
Login=${XM_LOGIN}
Password=${XM_PASSWORD}
Server=${XM_SERVER}
[Experts]
AllowLiveTrading=1
Enabled=1
[StartUp]
Expert=NTI\\NTI_LiquiditySweep
Symbol=${XM_SYMBOL:-GOLD}
Period=H1
EOF

echo "[5/6] systemd user service"
mkdir -p "$HOME/.config/systemd/user"
sed -e "s|__WINEPREFIX__|$WINEPREFIX|g" -e "s|__MT5_DIR__|$MT5_DIR|g" \
    "$REPO_DIR/deploy/linux/nti-mt5.service" > "$HOME/.config/systemd/user/nti-mt5.service"
systemctl --user daemon-reload
systemctl --user enable --now nti-mt5.service
sudo loginctl enable-linger "$USER"     # keep running after logout / reboot

echo "[6/6] Done. Logs: <Common>/Files/NTI/signals.csv  ->"
find "$WINEPREFIX/drive_c" -path "*MetaQuotes/Terminal/Common/Files/NTI*" 2>/dev/null | head -3
echo "Kill switch: touch \"\$(find $WINEPREFIX/drive_c -type d -path '*Terminal/Common/Files/NTI' | head -1)/KILL\""
