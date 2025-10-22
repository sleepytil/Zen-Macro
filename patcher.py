import os
import json
import subprocess

def popup(message, title):
    applescript = """
    
    display dialog "{message}" ¬
    with title "{title}" ¬
    with icon caution ¬
    buttons {{"OK"}}
    """.format(message=message, title=title)

    subprocess.call("osascript -e '{}'".format(applescript), shell=True)

try:
    os.mkdir("/Applications/Roblox.app/Contents/MacOS/ClientSettings")
except FileExistsError:
    print("ClientSettings folder already exists.")
flags = {"FStringDebugLuaLogLevel": "debug", "FStringDebugLuaLogPattern": "ExpChat/mountClientApp"}
try:
    with open("/Applications/Roblox.app/Contents/MacOS/ClientSettings/ClientAppSettings.json", "r") as f:
        existing_data = json.load(f)
except FileNotFoundError:
    existing_data = {}
existing_data.update(flags)
with open("/Applications/Roblox.app/Contents/MacOS/ClientSettings/ClientAppSettings.json", "w") as f:
    json.dump(existing_data, f, indent=4)
print("Successfully patched Roblox and added fast flags.")
popup("Roblox has successfully been patched.\nPlease restart Roblox for changes to take effect.", "Zen")