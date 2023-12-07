-- @description kusa_Split and implode from bank
-- @version 1.01
-- @author Kusa
-- @website https://thomashugofritz.wixsite.com/website
-- @donation https://paypal.me/tfkusa?country.x=FR&locale.x=fr_FR

function runExternalProgram()
    local reaperResourcePath = reaper.GetResourcePath()

    local relativeExecutablePath = "/Scripts/kusa_reascriptsWithDependencies/lib/banktotakes/build/mac/kusa_banktotakes" -- Mac executable path
    if reaper.GetOS() == "Win" then
        relativeExecutablePath = "\\Scripts\\kusa_reascriptsWithDependencies\\lib\\banktotakes\\build\\win\\kusa_banktotakes.exe" -- Windows executable path
    end

    local executablePath = reaperResourcePath .. relativeExecutablePath

    local command
    if reaper.GetOS() == "Win" then
        command = "\"" .. executablePath .. "\"" -- Windows execution command
    else
        command = "open \"" .. executablePath .. "\"" -- Mac execution command
    end

    os.execute(command)
end

runExternalProgram()
