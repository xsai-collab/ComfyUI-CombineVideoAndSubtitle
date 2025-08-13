import os
import sys
import torch
import subprocess
import time
import json
from utils.util_func import *

class CombineVideosFromFolder:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_video_path": ("STRING", {"default": ""}),
                "input_audio_path": ("STRING", {"default": ""}),
                "output_path": ("STRING", {"default": ""}),
                "input_video_format": (["mp4", "mov", "avi", "mkv"], {"default": "mp4"}),
                "input_audio_format": (["wav", "mp3", "m4a", "flac"], {"default": "wav"}),
                "output_filename": ("STRING", {"default": "output"}),
                "output_video_format": (["mp4", "mov", "avi", "mkv"], {"default": "mp4"}),
                "output_audio_format": (["wav", "mp3", "m4a", "flac"], {"default": "wav"})
            },
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_video_path",)
    FUNCTION = "combine_videos_from_folder"
    CATEGORY = "Combine Videos And Subtitles"
    OUTPUT_NODE = True
    
    def combine_videos_from_folder(self, input_video_path, input_audio_path, output_path, input_video_format, input_audio_format, output_filename, output_video_format, output_audio_format):
        try:
            input_video_path = os.path.abspath(input_video_path).strip()
            input_audio_path = os.path.abspath(input_audio_path).strip()

            # 检查input_video_path是否存在
            if not check_path_exists(input_video_path):
                raise ValueError(f"Input video path does not exist: {input_video_path}")
            # 检查input_video_path是否为目录
            if not check_path_is_dir(input_video_path):
                raise ValueError(f"Input video path is not a directory: {input_video_path}")
            
            # 获取input_video_path下的所有文件
            input_video_files = get_files(input_video_path, input_video_format)
            if len(input_video_files) == 0:
                raise ValueError(f"No video files found in the folder: {input_video_path}")

            # 如果用户提供了input_audio_path，则检查input_audio_path是否存在，是否是目录
            input_audio_files = []
            if input_audio_path != "":
                if not check_path_exists(input_audio_path):
                    raise ValueError(f"Input audio path does not exist: {input_audio_path}")
                if not check_path_is_dir(input_audio_path):
                    raise ValueError(f"Input audio path is not a directory: {input_audio_path}")
                input_audio_files = get_files(input_audio_path, input_audio_format)
                if len(input_audio_files) == 0:
                    raise ValueError(f"No audio files found in the folder: {input_audio_path}")


            # 检查output_path是否存在，如果不存在则创建
            if not check_path_exists(output_path):
                os.makedirs(output_path)

            video_filelist_filenames = os.path.join(output_path, f"input_video_filelist.txt")
            with open(video_filelist_filenames, "w") as f:
                for video_file in input_video_files:
                    f.write(video_file + "\n")

            if len(input_audio_files) > 0:
                audio_filelist_filenames = os.path.join(output_path, f"input_audio_filelist.txt")
                with open(audio_filelist_filenames, "w") as f:
                    for audio_file in input_audio_files:
                        f.write(audio_file + "\n")

            time_str = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            output_video_filename = output_filename + "_" + time_str + "." + output_video_format
            output_video_path = os.path.join(output_path, output_video_filename)
            if len(input_audio_files) > 0:
                output_audio_filename = output_filename + "_" + time_str + "." + output_audio_format
                output_audio_path = os.path.join(output_path, output_audio_filename)

            video_combine_command = f"ffmpeg -f concat -safe 0 -i {video_filelist_filenames} -c copy {output_video_path}"
            if len(input_audio_files) > 0:
                audio_combine_command = f"ffmpeg -f concat -safe 0 -i {audio_filelist_filenames} -c copy {output_audio_path}"
                video_audio_combine_command = f"ffmpeg -i {output_video_path} -i {output_audio_path} -c copy {output_path}/{output_filename}_audio_combined.{output_video_format}"

            result = subprocess.run(video_combine_command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                raise ValueError(f"Error: {result.stderr}")
            if len(input_audio_files) > 0:
                result = subprocess.run(audio_combine_command, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    raise ValueError(f"Error: {result.stderr}")
                else:
                    result = subprocess.run(video_audio_combine_command, shell=True, capture_output=True, text=True)
                    if result.returncode != 0:
                        raise ValueError(f"Error: {result.stderr}")

            return (output_video_path,)
        except Exception as e:
            raise ValueError(f"Error: {e}")
        

NODE_CLASS_MAPPINGS = {
    "CombineVideosFromFolder": CombineVideosFromFolder
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "CombineVideosFromFolder": "Combine Videos From Folder"
}