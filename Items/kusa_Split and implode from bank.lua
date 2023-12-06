-- @description kusa_Split and implode from bank
-- @version 1.0
-- @author Kusa
-- @website https://thomashugofritz.wixsite.com/website
-- @donation https://paypal.me/tfkusa?country.x=FR&locale.x=fr_FR

function run_external_program()
    -- Use REAPER's API to get REAPER's resource path
    local reaper_resource_path = reaper.GetResourcePath()

    -- Specify the relative path to the standalone script within the 'Python' subfolder
    local relative_script_path = "/Scripts/kusa_reascriptsWithDependencies/lib/kusa_banktotakes.py"
    if reaper.GetOS() == "Win" then
        relative_script_path = "\\Scripts\\kusa_reascriptsWithDependencies\\lib\\kusa_banktotakes.py"
    end

    -- Combine them to form the full path to the script
    local script_path = reaper_resource_path .. relative_script_path

    -- Determine the command based on the operating system
    local command
    if reaper.GetOS() == "Win" then
        -- Windows command
        command = "python \"" .. script_path .. "\""
    else
        -- macOS command (AppleScript)
        local applescript_command = "tell application \"Terminal\" to do script \"python3 '" .. script_path .. "'\""
        command = "osascript -e " .. string.format("%q", applescript_command)
    end

    -- Execute the command
    os.execute(command)
end

run_external_program()
