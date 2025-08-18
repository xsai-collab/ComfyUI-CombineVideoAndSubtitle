import os
import sys
import torch
import subprocess
import time
import json
import logging
import faster_whisper
import folder_paths

from .utils.util_func import *
from typing import List, Tuple
from comfy.utils import ProgressBar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models_path = folder_paths.models_dir
input_path = folder_paths.get_input_directory()
output_path = folder_paths.get_output_directory()

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
                "input_video_format": (["mp4", "mov", "avi", "mkv", "m4v"], {"default": "mp4"}),
                "input_audio_format": (["wav", "mp3", "m4a", "flac"], {"default": "wav"}),
                "output_filename": ("STRING", {"default": "output"}),
                "output_video_format": (["mp4", "mov", "avi", "mkv", "m4v"], {"default": "mp4"}),
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
                input_audio_path = os.path.abspath(input_audio_path).strip()
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
                    f.write(f"file '{video_file}'\n")

            if len(input_audio_files) > 0:
                audio_filelist_filenames = os.path.join(output_path, f"input_audio_filelist.txt")
                with open(audio_filelist_filenames, "w") as f:
                    for audio_file in input_audio_files:
                        f.write(f"file '{audio_file}'\n")

            time_str = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            output_video_filename = output_filename + "_" + time_str + "." + output_video_format
            output_video_path = os.path.join(output_path, output_video_filename)
            if len(input_audio_files) > 0:
                output_audio_filename = output_filename + "_" + time_str + "." + output_audio_format
                output_audio_path = os.path.join(output_path, output_audio_filename)

            video_combine_command = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", video_filelist_filenames, "-c", "copy", output_video_path]
            if len(input_audio_files) > 0:
                audio_combine_command = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", audio_filelist_filenames, "-c", "copy", output_audio_path]
                video_audio_combine_command = ["ffmpeg", "-i", output_video_path, "-i", output_audio_path, "-c", "copy", output_path, f"{output_filename}_audio_combined.{output_video_format}"]

            result = subprocess.run(video_combine_command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            if result.returncode != 0:
                raise ValueError(f"Error: {result.stderr}")
            if len(input_audio_files) > 0:
                result = subprocess.run(audio_combine_command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                if result.returncode != 0:
                    raise ValueError(f"Error: {result.stderr}")
                else:
                    result = subprocess.run(video_audio_combine_command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                    if result.returncode != 0:
                        raise ValueError(f"Error: {result.stderr}")

            return (output_video_path,)
        except Exception as e:
            raise ValueError(f"Error: {e}")
        

class getSubtitlesFromVideo:
    def __init__(self):
        self.faster_whisper_model_dir = os.path.join(models_path, "faster-whisper")
        whisper_models = list(model for model in faster_whisper.available_models())
        self.whisper_models = whisper_models

        language_list = list(language for language in faster_whisper.WhisperModel.supported_languages())
        self.language_list = language_list.append("auto")
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_file_path": ("STRING", ),
                "whisper_model": (cls.whisper_models, ),
                "device": (["cpu", "cuda", "auto"], {"default": "auto"}),
                "language": (cls.language_list, ),
                "task": (["transcribe", "translate"], {"default": "transcribe"}),
                "output_path": ("STRING", {"default": ""}),
                "output_filename": ("STRING", {"default": "output"}),
                "output_format": (["srt", "vtt"], {"default": "srt"})
            },
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_subtitles_path",)
    FUNCTION = "get_subtitles_from_video"
    CATEGORY = "Combine Videos And Subtitles"
    OUTPUT_NODE = True
    
    def get_subtitles_from_video(self, input_file_path, whisper_model, device, language, task, output_path, output_filename, output_format) -> Tuple[List]:
        try:
            input_file_path = os.path.abspath(input_file_path).strip()
            if not check_path_exists(input_file_path):
                raise ValueError(f"Input file path does not exist: {input_file_path}")
            if not check_path_is_file(input_file_path):
                raise ValueError(f"Input file path is not a file: {input_file_path}")
            
            if output_path == "":
                raise ValueError("Output path is not inputed")
            
            if output_filename == "":
                raise ValueError("Output filename is not inputed")
            
            if output_format == "":
                raise ValueError("Output format is not selected")
            
            if check_path_is_file(output_path):
                raise ValueError(f"Output path is a file: {output_path}")
            
            if not check_path_exists(output_path):
                os.makedirs(output_path)
            
            output_file_path = os.path.join(output_path, f"{output_filename}.{output_format}")

            if language == "auto":
                language = None

            fast_whisper_model = self.loadAndDowndModels(whisper_model, device, self.faster_whisper_model_dir)

            # 使用fast_whisper_model进行语音识别
            segments, info = fast_whisper_model.transcribe(input_file_path, language=language, task=task)

            # 创建进度条
            comfy_pbar = ProgressBar(info.duration)

            # 将识别结果转换为字典列表
            transcriptions = []
            for segment in segments:
                comfy_pbar.update_absolute(segment.end)
                transcriptions.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                })

            # 将识别结果写入文件
            self.writeSubtitlesToFile(transcriptions, output_file_path, output_format)

            return (output_file_path,)

        except Exception as e:
            raise ValueError(f"Error: {e}")
    
    @staticmethod
    def loadAndDowndModels(whisper_model, device, download_root) -> faster_whisper.WhisperModel:
        if not check_path_exists(download_root):
            os.makedirs(download_root)
        fast_whisper_model = faster_whisper.WhisperModel(
            model_size_or_path=whisper_model,
            device=device,
            download_root=download_root,
            local_files_only=False
        )
        return fast_whisper_model
    
    @staticmethod
    def writeSubtitlesToFile(self, subtitles, output_file_path, output_format):
        subtitle_text = ""
        if output_format == "srt":
            start_text = ""
        elif output_format == "vtt":
            start_text = "WEBVTT\n\n"

        subtitle_text += start_text

        for i, subtitle in enumerate(subtitles):
            start_time = self.format_time(subtitle["start"], output_format)
            end_time = self.format_time(subtitle["end"], output_format)
            text = subtitle["text"].strip()

            subtitle_text += f"{i+1}\n"
            subtitle_text += f"{start_time} --> {end_time}\n"
            subtitle_text += f"{text}\n\n"
            
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(subtitle_text)

    @staticmethod
    def format_time(time, output_format):
        hours = int(time // 3600)
        minutes = int((time % 3600) // 60)
        seconds = int(time % 60)
        milliseconds = int((time - int(time)) * 1000)
        if output_format == "srt":
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
        elif output_format == "vtt":
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        else:
            raise ValueError(f"Invalid output format: {output_format}")


NODE_CLASS_MAPPINGS = {
    "CombineVideosFromFolder": CombineVideosFromFolder,
    "getSubtitlesFromVideo": getSubtitlesFromVideo
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "CombineVideosFromFolder": "Combine Videos From Folder",
    "getSubtitlesFromVideo": "Get Subtitles From Video"
}