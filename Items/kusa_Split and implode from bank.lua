-- @description kusa_Split and implode from bank
-- @version 1.01
-- @author Kusa
-- @website https://thomashugofritz.wixsite.com/website
-- @donation https://paypal.me/tfkusa?country.x=FR&locale.x=fr_FR

function runExternalProgram()
    local reaperResourcePath = reaper.GetResourcePath()

    local relativeScriptPath = "/Scripts/kusa_reascriptsWithDependencies/lib/kusa_banktotakes.py"
    if reaper.GetOS() == "Win" then
        relativeScriptPath = "\\Scripts\\kusa_reascriptsWithDependencies\\lib\\kusa_banktotakes.py"
    end

    local scriptPath = reaperResourcePath .. relativeScriptPath

    local command
    if reaper.GetOS() == "Win" then
        command = "python \"" .. scriptPath .. "\""
    else
        local appleScriptCommand = "tell application \"Terminal\" to do script \"python3 '" .. scriptPath .. "'\""
        command = "osascript -e " .. string.format("%q", appleScriptCommand)
    end

    os.execute(command)
end

runExternalProgram()
