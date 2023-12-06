# @description kusa_Split and implode from bank_main
# @version 1.0
# @author Kusa
# @website https://thomashugofritz.wixsite.com/website
# @donation https://paypal.me/tfkusa?country.x=FR&locale.x=fr_FR

import reapy
import os
import shutil
from pydub.utils import make_chunks
from pydub import AudioSegment
from pydub import silence
from pydub.silence import split_on_silence
from scipy.io import wavfile
import numpy as np



def get_project_folder():
    """ Get the folder of the current REAPER project. """
    with reapy.inside_reaper():
        project = reapy.Project()
        buffer_size = 512
        project_path_buffer = reapy.reascript_api.GetProjectPath("", buffer_size)
        project_path = project_path_buffer[0]

        if project_path:
            return os.path.dirname(project_path)
        else:
            return None

def create_temp_folder_in_project_folder():
    """ Create a temporary folder inside the REAPER project's folder. """
    project_folder = get_project_folder()
    if project_folder:
        temp_folder_name = "tempSplit"
        temp_folder_path = os.path.join(project_folder, temp_folder_name)
        os.makedirs(temp_folder_path, exist_ok=True)
        return temp_folder_path
    else:
        raise FileNotFoundError("REAPER project folder not found.")

def set_render_settings(project, temp_folder):
    with reapy.inside_reaper():

        # Apply the new render settings
        reapy.reascript_api.GetSetProjectInfo(project.id, "RENDER_SETTINGS", 32, True)

        # Set render path
        project.set_info_string("RENDER_FILE", temp_folder)

        # Set render pattern (this is an example, adjust as needed)
        reapy.reascript_api.GetSetProjectInfo_String(project, 'RENDER_PATTERN', "temp_render", True)


def split_item_on_silence(project, original_item, temp_file_path):
    sound = AudioSegment.from_wav(temp_file_path)
    silence_threshold = -50  # dB

    # Detect silence and get split points
    chunks = split_on_silence(sound, silence_thresh=silence_threshold)

    # Diagnostic print
    print(f"Number of chunks found: {len(chunks)}")

    if not chunks:
        print("No silent sections found for splitting.")
        return

    split_points = []
    cumulative_length = 0

    for i, chunk in enumerate(chunks[:-1]):  # Exclude the last chunk
        cumulative_length += len(chunk)
        split_point = cumulative_length / 1000.0  # Convert to seconds
        split_points.append(split_point)

        # Diagnostic print
        print(f"Chunk {i}, Length: {len(chunk)}, Split at: {split_point}")

    # Translate split points to REAPER and split the item
    for split_point in split_points:
        actual_split_point = original_item.position + split_point
        print(f"Splitting at REAPER position: {actual_split_point}")

        # Find and split the item at the actual split point
        for item in project.items:
            if item.position <= actual_split_point <= (item.position + item.length):
                item.split(actual_split_point)
                break

    print("Items have been split.")



def remove_silence_from_item(project, item, temp_file_path, silence_threshold=-50, min_silence_len=500):
    """
    Removes silence from an audio item in REAPER.
    
    Parameters:
    project: reapy.Project instance
    item: reapy.Item instance
    temp_file_path: Path to the temporary audio file
    silence_threshold: Silence threshold in dB
    min_silence_len: Minimum length of a silence to be considered (in milliseconds)
    """

    # Load the audio file
    sound = AudioSegment.from_wav(temp_file_path)

    # Find non-silent chunks
    non_silent_chunks = silence.split_on_silence(sound, 
                                                 min_silence_len=min_silence_len,
                                                 silence_thresh=silence_threshold)

    # Combine non-silent chunks
    combined = AudioSegment.empty()
    for chunk in non_silent_chunks:
        combined += chunk

    # Export the combined audio back to the temp file
    combined.export(temp_file_path, format="wav")

    # Replace the original item's source with the new audio file
    # Note: This will create a new take in the item
    project.perform_action(40129)  # Unselect all items
    item.selected = True
    reapy.reascript_api.InsertMedia(temp_file_path, 0)  # Add to current track

    print("Silence removed from item.")  

def trim_leading_silence(sound, silence_threshold=-50.0, chunk_size=10):
    """
    Trims leading silence from a sound chunk.

    Parameters:
    sound: pydub.AudioSegment instance
    silence_threshold: dB level below which the sound is considered silence
    chunk_size: size of chunks to use when analyzing sound (in milliseconds)

    Returns:
    Trimmed pydub.AudioSegment
    """
    start_trim = 0
    for i in range(0, len(sound), chunk_size):
        if sound[i:i+chunk_size].dBFS > silence_threshold:
            start_trim = i
            break
    return sound[start_trim:]


def find_peak_segment_start(chunk, window_size=100000):
    """Find the start position of the peak amplitude segment."""
    _, data = wavfile.read(chunk.export(format="wav"))
    peak_index = np.argmax(np.abs(data))
    start_index = max(0, peak_index - window_size // 2)
    return start_index / chunk.frame_rate  # in seconds


def create_takes_for_non_silent_parts(project, item, temp_file_path, silence_threshold=-50, min_silence_len=700):
    sound = AudioSegment.from_wav(temp_file_path)
    non_silent_chunks = silence.split_on_silence(sound, min_silence_len=min_silence_len, silence_thresh=silence_threshold)

    segment_starts = [find_peak_segment_start(chunk) for chunk in non_silent_chunks]
    farthest_segment_start = max(segment_starts)  # Chunk whose peak segment is farthest from the start
    max_chunk_length = max(len(chunk) for chunk in non_silent_chunks)

    project.perform_action(40289)  # Unselect all items
    item.selected = True

    for i, (chunk, segment_start) in enumerate(zip(non_silent_chunks, segment_starts)):
        start_padding = (farthest_segment_start - segment_start) * 1000  # Convert to milliseconds
        padded_chunk = AudioSegment.silent(duration=start_padding) + chunk

        total_length = max_chunk_length + (farthest_segment_start * 1000)
        end_padding = total_length - len(padded_chunk)
        padded_chunk += AudioSegment.silent(duration=end_padding)

        chunk_file_path = os.path.join(os.path.dirname(temp_file_path), f"chunk_{i}.wav")
        padded_chunk.export(chunk_file_path, format="wav")
        reapy.reascript_api.InsertMedia(chunk_file_path, 0)  # Add to current track as a new take



def delete_temp_folder(temp_folder):
    shutil.rmtree(temp_folder)


def add_region_around_item(project, item):
    """Add a region around the selected item and return the region ID."""
    with reapy.inside_reaper():
        is_region = True  # True for region, False for marker
        region_id = reapy.reascript_api.AddProjectMarker2(project.id, is_region, item.position, item.position + item.length, "", 0, -1)
        return region_id


def set_region_render_matrix(project, region_id, track):
    with reapy.inside_reaper():
        # Get project reference
        project_ref = project.id
        track_ref = track.id
        # Set the track active in the region render matrix
        reapy.reascript_api.SetRegionRenderMatrix(project_ref, region_id, track_ref, 1)  # 1 to include, 0 to exclude


def preRender(project):
    # Create a temporary folder
    temp_folder = create_temp_folder_in_project_folder()   

    # Set render settings
    set_render_settings(project, temp_folder)
    return temp_folder



def render():
    # Trigger rendering (replace with your action ID)
    reapy.reascript_api.Main_OnCommand(42230,0)

def processAudio(temp_folder, project, item):
    temp_file_path = os.path.join(temp_folder, "temp_render.wav")
    # Load the audio file
    sound = AudioSegment.from_wav(temp_file_path)
    # Add one second of silence at the beginning
    sound_with_silence = AudioSegment.silent(duration=1000) + sound
    # Export the audio with added silence back to the temp file
    sound_with_silence.export(temp_file_path, format="wav")
    
    create_takes_for_non_silent_parts(project, item, temp_file_path, silence_threshold=-50, min_silence_len=700)
    delete_temp_folder(temp_folder)


def main():
    with reapy.inside_reaper():
        project = reapy.Project()
        if project.selected_items:
            item = project.selected_items[0]
            temp_folder = preRender(project)
            render()
            reapy.reascript_api.Main_OnCommand(40006, 0)  # Command to remove selected items
            processAudio(temp_folder, project, item)
            project.perform_action(40543)
        else:
            project.perform_action(40435)


if __name__ == "__main__":
    main()

