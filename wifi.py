"""
Shared WiFi switching module for macOS.
Switches between home WiFi and iPhone hotspot using AppleScript UI
automation and networksetup.

Requires: System Settings -> Privacy & Security -> Accessibility -> Terminal
"""

import socket
import subprocess
import time

# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

HOTSPOT_NETWORKS = [
    "Sohel\u2019s iPhone",    # curly apostrophe (Apple default)
    "Sohel's iPhone",          # straight apostrophe fallback
]

HOME_NETWORKS = [
    {"ssid": "TechnionWiFi", "password": "mypass", "username": "sohel@campus.technion.ac.il"},
]

WIFI_INTERFACE = "en0"
NETWORK_RETRY_ATTEMPTS = 3
NETWORK_RETRY_DELAY = 3


# ---------------------------------------------------------------------
# LOW-LEVEL HELPERS
# ---------------------------------------------------------------------

def click_wifi_network(network_name):
    """
    Open the WiFi menu in Control Center and click a network by
    AXIdentifier. Returns True if clicked successfully.
    """
    ax_id = "wifi-network-" + network_name
    ax_id_escaped = ax_id.replace('"', '\\"')
    script = '''
    tell application "System Events"
        tell process "ControlCenter"
            set menuItems to every menu bar item of menu bar 1
            repeat with mi in menuItems
                try
                    if value of attribute "AXIdentifier" of mi is "com.apple.menuextra.wifi" then
                        click mi
                        exit repeat
                    end if
                end try
            end repeat

            delay 1.5

            tell window 1
                set allElements to entire contents
                set found to false
                repeat with elem in allElements
                    try
                        if class of elem is checkbox then
                            set elemId to value of attribute "AXIdentifier" of elem
                            if elemId is "''' + ax_id_escaped + '''" then
                                click elem
                                set found to true
                                exit repeat
                            end if
                        end if
                    end try
                end repeat

                if not found then
                    key code 53
                end if
            end tell

            if found then
                delay 0.5
                key code 53
            end if

            return found
        end tell
    end tell
    '''

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=30,
        )
        return "true" in result.stdout.strip().lower()
    except Exception:
        return False


def networksetup_connect(ssid, password="", username=""):
    """
    Connect to a WiFi network via networksetup.
    For enterprise/802.1X networks, pass username (email).
    """
    cmd = ["networksetup", "-setairportnetwork", WIFI_INTERFACE, ssid]
    if password:
        cmd.append(password)
    if username:
        cmd.append(username)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0
    except Exception:
        return False


# ---------------------------------------------------------------------
# CONNECTIVITY CHECK
# ---------------------------------------------------------------------

def wait_for_connectivity(timeout=30, interval=2):
    """Ping + DNS check until the network is actually usable."""
    targets = ["1.1.1.1", "8.8.8.8", "api.github.com"]
    deadline = time.time() + timeout
    while time.time() < deadline:
        for target in targets:
            try:
                result = subprocess.run(
                    ["ping", "-c", "1", "-W", "5", target],
                    capture_output=True, timeout=10,
                )
                if result.returncode == 0:
                    print(f"  Connectivity OK ({target})")
                    return True
            except Exception:
                continue
        # Fallback: try DNS resolution
        try:
            socket.getaddrinfo("api.github.com", 443)
            print("  DNS ready (api.github.com resolved)")
            return True
        except socket.gaierror:
            pass
        time.sleep(interval)
    print(f"  WARNING: no connectivity after {timeout}s — continuing anyway")
    return False


# ---------------------------------------------------------------------
# HIGH-LEVEL SWITCHING
# ---------------------------------------------------------------------

def switch_to_hotspot():
    """Try each hotspot network in order, with retries."""
    for ssid in HOTSPOT_NETWORKS:
        for attempt in range(1, NETWORK_RETRY_ATTEMPTS + 1):
            tag = "(" + str(attempt) + "/" + str(NETWORK_RETRY_ATTEMPTS) + ")"
            print("  Trying hotspot \"" + ssid + "\" " + tag + " ...")
            if click_wifi_network(ssid):
                time.sleep(5)
                print("  Connected to \"" + ssid + "\"")
                wait_for_connectivity()
                return True
            if attempt < NETWORK_RETRY_ATTEMPTS:
                print("  Retrying in " + str(NETWORK_RETRY_DELAY) + "s ...")
                time.sleep(NETWORK_RETRY_DELAY)
        print("  Failed all attempts for \"" + ssid + "\"")

    print("  All hotspot networks failed - continuing on current network")
    return False


def switch_to_home():
    """Try each home network in order, with retries."""
    for net in HOME_NETWORKS:
        ssid = net["ssid"]
        password = net.get("password", "")
        username = net.get("username", "")
        for attempt in range(1, NETWORK_RETRY_ATTEMPTS + 1):
            tag = "(" + str(attempt) + "/" + str(NETWORK_RETRY_ATTEMPTS) + ")"
            print("  Trying home WiFi \"" + ssid + "\" " + tag + " ...")

            if password or username:
                success = networksetup_connect(ssid, password, username)
            else:
                success = networksetup_connect(ssid)
            if not success:
                success = click_wifi_network(ssid)

            if success:
                time.sleep(4)
                print("  Connected to \"" + ssid + "\"")
                return True
            if attempt < NETWORK_RETRY_ATTEMPTS:
                print("  Retrying in " + str(NETWORK_RETRY_DELAY) + "s ...")
                time.sleep(NETWORK_RETRY_DELAY)
        print("  Failed all attempts for \"" + ssid + "\"")

    print("  All home networks failed - reconnect manually!")
    return False
