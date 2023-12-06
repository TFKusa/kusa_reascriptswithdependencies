# @description kusa_Split and implode from bank
# @version 1.0
# @author Kusa
# @website https://thomashugofritz.wixsite.com/website
# @donation https://paypal.me/tfkusa?country.x=FR&locale.x=fr_FR

import subprocess
import reapy

def run_external_program():
    # Use reapy to get REAPER's resource path
    reaper_resource_path = reapy.reascript_api.GetResourcePath()

    # Specify the relative path to the standalone script within the 'Python' subfolder
    relative_script_path = "/Scripts/kusa_reascriptsWithDependencies/lib/kusa_banktotakes.py"

    # Combine them to form the full path to the script
    script_path = reaper_resource_path + relative_script_path

    print(script_path)

    # Properly quote the path
    quoted_script_path = f"'{script_path}'"

    # Construct AppleScript command to run the script in Terminal
    applescript_command = f"""
    tell application "Terminal"
        do script "python3 {quoted_script_path}"
    end tell
    """
    subprocess.run(["osascript", "-e", applescript_command])

run_external_program()
