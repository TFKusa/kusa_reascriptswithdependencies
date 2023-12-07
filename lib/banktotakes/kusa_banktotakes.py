# @description kusa_Split and implode from bank_main
# @version 1.01
# @author Kusa
# @website https://thomashugofritz.wixsite.com/website
# @donation https://paypal.me/tfkusa?country.x=FR&locale.x=fr_FR

import reapy
import os
import shutil
from pydub import AudioSegment
from pydub import silence
from pydub.silence import split_on_silence
from scipy.io import wavfile
import numpy as np
from pydub.utils import mediainfo


def getProjectFolder():
    with reapy.inside_reaper():
        bufferSize = 512
        projectPathBuffer = reapy.reascript_api.GetProjectPath("", bufferSize)
        projectPath = projectPathBuffer[0]

        if projectPath:
            return os.path.dirname(projectPath)
        else:
            return None

def createTempFolderInProjectFolder():
    projectFolder = getProjectFolder()
    if projectFolder:
        tempFolderName = "tempSplit"
        tempFolderPath = os.path.join(projectFolder, tempFolderName)
        os.makedirs(tempFolderPath, exist_ok=True)
        return tempFolderPath
    else:
        raise FileNotFoundError("REAPER project folder not found.")

def getAudioFilePathOfSelectedItem(project):
    with reapy.inside_reaper():
        if not project.selected_items:
            print("No item is selected.")
            return None

        selectedItem = project.selected_items[0]

        activeTake = selectedItem.active_take

        if activeTake and activeTake.source:
            source = activeTake.source

            return source.filename
        else:
            raise ValueError("Selected item does not have an active take or source.")

def getAudioSampleRate(filePath):
    info = mediainfo(filePath)
    return int(info['sample_rate'])

def setRenderSettings(project, tempFolder):
    with reapy.inside_reaper():
        audioFilePath = getAudioFilePathOfSelectedItem(project)
        sampleRate = getAudioSampleRate(audioFilePath)
        project.set_info_value("RENDER_SRATE", sampleRate)

        reapy.reascript_api.GetSetProjectInfo(project.id, "RENDER_SETTINGS", 32, True)

        project.set_info_string("RENDER_FILE", tempFolder)

        reapy.reascript_api.GetSetProjectInfo_String(project, 'RENDER_PATTERN', "temp_render", True)

def preRender(project):
    tempFolder = createTempFolderInProjectFolder()   

    setRenderSettings(project, tempFolder)
    return tempFolder

def render():
    with reapy.inside_reaper():
        reapy.reascript_api.Main_OnCommand(42230,0)

def findPeakSegmentStart(chunk, windowSize=100000):
    _, data = wavfile.read(chunk.export(format="wav"))
    peakIndex = np.argmax(np.abs(data))
    startIndex = max(0, peakIndex - windowSize // 2)
    return startIndex / chunk.frame_rate  # in seconds

def createTakesForNonSilentParts(project, item, tempFilePath, silenceThreshold=-50, minSilenceLen=700):
    sound = AudioSegment.from_wav(tempFilePath)
    nonSilentChunks = silence.split_on_silence(sound, min_silence_len=minSilenceLen, silence_thresh=silenceThreshold)

    segmentStarts = [findPeakSegmentStart(chunk) for chunk in nonSilentChunks]
    farthestSegmentStart = max(segmentStarts)
    maxChunkLength = max(len(chunk) for chunk in nonSilentChunks)

    project.perform_action(40289)
    item.selected = True

    for i, (chunk, segmentStart) in enumerate(zip(nonSilentChunks, segmentStarts)):
        startPadding = (farthestSegmentStart - segmentStart) * 1000  # Convert to milliseconds
        paddedChunk = AudioSegment.silent(duration=startPadding) + chunk

        totalLength = maxChunkLength + (farthestSegmentStart * 1000)
        endPadding = totalLength - len(paddedChunk)
        paddedChunk += AudioSegment.silent(duration=endPadding)

        chunkFilePath = os.path.join(os.path.dirname(tempFilePath), f"chunk_{i}.wav")
        paddedChunk.export(chunkFilePath, format="wav")
        with reapy.inside_reaper():
            reapy.reascript_api.InsertMedia(chunkFilePath, 0)

def deleteTempFolder(tempFolder):
    shutil.rmtree(tempFolder)

def processAudio(tempFolder, project, item):
    tempFilePath = os.path.join(tempFolder, "temp_render.wav")
    sound = AudioSegment.from_wav(tempFilePath)
    soundWithSilence = AudioSegment.silent(duration=1000) + sound
    soundWithSilence.export(tempFilePath, format="wav")
    
    createTakesForNonSilentParts(project, item, tempFilePath, silenceThreshold=-50, minSilenceLen=700)
    deleteTempFolder(tempFolder)

def main():
    with reapy.inside_reaper():
        project = reapy.Project()
        if project.selected_items:
            item = project.selected_items[0]
            tempFolder = preRender(project)
            render()
            reapy.reascript_api.Main_OnCommand(40006, 0)
            processAudio(tempFolder, project, item)
            project.perform_action(40543)
        else:
            project.perform_action(40435)

if __name__ == "__main__":
    main()