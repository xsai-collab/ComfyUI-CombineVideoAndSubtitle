import os
import sys
import torch
import subprocess
import time
import json
import logging
import faster_whisper

from .utils.util_func import *
from typing import List, Tuple
from comfy.utils import ProgressBar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_file_path": ("STRING", ),
                "fast_whisper_model": ("FASTERWHISPERMODEL", ),
                "output_path": ("STRING", {"default": ""}),
                "output_filename": ("STRING", {"default": "output"}),
                "output_format": (["srt", "ass", "ssa", "sub"], {"default": "srt"})
            },
            "optional": {
                "language": ("STRING", {"default": "auto"}),
                "task": (["transcribe", "translate"], {"default": "transcribe"}),
                "beam_size": ("INT", {"default": 5, "min": 1, "max": 10}),
                "log_prob_threshold": ("FLOAT", {"default": -1.0, "min": -1.0, "max": 1.0}),
                "no_speech_threshold": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.0}),
                "best_of": ("INT", {"default": 1, "min": 1, "max": 10}),
                "patience": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0}),
                "temperature": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0}),
                "compression_ratio_threshold": ("FLOAT", {"default": 2.0, "min": 0.0, "max": 10.0}),
                "length_penalty": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0}),
                "repetition_penalty": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0}),
                "no_repeat_ngram_size": ("INT", {"default": 0, "min": 0, "max": 10}),
                "prefix": ("STRING", {"default": ""}),
                "suppress_blank": ("BOOLEAN", {"default": True}),
                "suppress_tokens": ("STRING", {"default": "[-1]"}),
                "max_initial_timestamp": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 10.0}),
                "word_timestamps": ("BOOLEAN", {"default": False}),
                "prepend_punctuations": ("STRING", {"default": "\"'“¿([{-"}),
                "append_punctuations": ("STRING", {"default": "\"'.。,，!！?？:：”)]}、"}),
                "max_new_tokens": ("INT", {"default": -999, "min": -1000, "max": 10000}),
                "chunk_length": ("INT", {"default": -999, "min": -1000, "max": 10000}),
                "hallucination_silence_threshold": ("FLOAT", {"default": -999.0, "min": -1000.0, "max": 1000.0}),
                "hotwords": ("STRING", {"default": ""}),
                "language_detection_threshold": ("FLOAT", {"default": -999.0, "min": -1000.0, "max": 1000.0}),
                "language_detection_segments": ("INT", {"default": 1, "min": 1, "max": 100}),
                "prompt_reset_on_temperature": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
                "condition_on_previous_text": ("BOOLEAN", {"default": True}),
                "initial_prompt": ("STRING", {"default": ""}),
                "without_timestamps": ("BOOLEAN", {"default": False}),
                "vad_filter": ("BOOLEAN", {"default": False}),
                "vad_parameters": ("STRING", {"default": ""}),
                "clip_timestamps": ("STRING", {"default": "0"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_subtitles_path",)
    FUNCTION = "get_subtitles_from_video"
    CATEGORY = "Combine Videos And Subtitles"
    OUTPUT_NODE = True
    
    def get_subtitles_from_video(self, input_file_path, fast_whisper_model:faster_whisper.WhisperModel, output_path, output_filename, output_format, **params, ) -> Tuple[List]:
        params = self.collect_params(params)
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

            logger.info(f"params: {params}")
            # 使用fast_whisper_model进行语音识别
            segments, info = fast_whisper_model.transcribe(input_file_path, **params)

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

            return (output_file_path,)

        except Exception as e:
            raise ValueError(f"Error: {e}")
    
    @staticmethod
    def collect_params(params):
        if "language" in params and params["language"] == "auto":
            params["language"] = None
        if "suppress_tokens" in params:
            params["suppress_tokens"] = eval(params["suppress_tokens"])
        if "prefix" in params and not params["prefix"]:
            params["prefix"] = None
        if "hotwords" in params and not params["hotwords"]:
            params["hotwords"] = None
        if "initial_prompt" in params and not params["initial_prompt"]:
            params["initial_prompt"] = None
        if "vad_parameters" in params and not params["vad_parameters"]:
            params["vad_parameters"] = None
        if "max_new_tokens" in params and params["max_new_tokens"] == -999:
            params["max_new_tokens"] = None
        if "chunk_length" in params and params["chunk_length"] == -999:
            params["chunk_length"] = None
        if "hallucination_silence_threshold" in params and params["hallucination_silence_threshold"] == -999.0:
            params["hallucination_silence_threshold"] = None
        if "language_detection_threshold" in params and params["language_detection_threshold"] == -999.0:
            params["language_detection_threshold"] = None
        return params

NODE_CLASS_MAPPINGS = {
    "CombineVideosFromFolder": CombineVideosFromFolder,
    "getSubtitlesFromVideo": getSubtitlesFromVideo
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "CombineVideosFromFolder": "Combine Videos From Folder",
    "getSubtitlesFromVideo": "Get Subtitles From Video"
}