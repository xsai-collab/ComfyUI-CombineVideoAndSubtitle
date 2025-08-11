import os
import sys
import torch
import subprocess
import time
import json

class CombineVideosFromFolder:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"default": ""}),
                "audio_path": ("STRING", {"default": ""}),
                "output_path": ("STRING", {"default": ""}),
                "output_duration": ("INT", {"default": 10, "min": 1, "max": 1000}),
                "output_fps": ("INT", {"default": 30, "min": 1, "max": 100}),
                "output_quality": ("INT", {"default": 10, "min": 1, "max": 100}),
                "output_bitrate": ("INT", {"default": 1000, "min": 100, "max": 10000}),
                "input_format": ("STRING", {"default": "mp4", "options": ["mp4", "mov", "avi", "mkv"]}),
                "output_filename": ("STRING", {"default": "output.mp4"}),
                "output_format": ("STRING", {"default": "mp4", "options": ["mp4", "mov", "avi", "mkv"]}),
            },
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_video_path",)
    FUNCTION = "combine_videos_from_folder"
    CATEGORY = "Combine Videos And Subtitles"
    OUTPUT_NODE = True
    
    def combine_videos_from_folder(self, video_path, audio_path, output_path, output_duration, output_fps, output_quality, output_bitrate, input_format, output_filename, output_format):
        try:
            video_path = os.path.abspath(video_path).strip()
            audio_path = os.path.abspath(audio_path).strip()
            output_path = os.path.abspath(output_path).strip()
            output_filename = os.path.abspath(output_filename).strip()
            output_format = os.path.abspath(output_format).strip()
            input_format = os.path.abspath(input_format).strip()
            output_duration = int(output_duration)
            output_fps = int(output_fps)
            if len(video_path) == 0 or len(audio_path) == 0:
                raise ValueError("No videos or audio files found in the folder")
            video_path.sort()
            audio_path.sort()
            video_path = [os.path.join(video_path, f) for f in video_path]
            audio_path = [os.path.join(audio_path, f) for f in audio_path]
            for video_path, audio_path in zip(video_path, audio_path):
                video_path = os.path.join(video_path, f)
                audio_path = os.path.join(audio_path, f)
                output_path = os.path.join(output_path, f)
                output_filename = os.path.join(output_filename, f)
        except Exception as e:
            raise ValueError(f"Error: {e}")
        

NODE_CLASS_MAPPINGS = {
    "CombineVideosFromFolder": CombineVideosFromFolder
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "CombineVideosFromFolder": "Combine Videos From Folder"
}