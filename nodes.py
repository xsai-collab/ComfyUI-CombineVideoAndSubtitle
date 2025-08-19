import os
import subprocess
import time
import logging
import faster_whisper
import folder_paths
import shutil

from .utils.util_func import *
from typing import List, Tuple
from comfy.utils import ProgressBar

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

# 设置logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models_path = folder_paths.models_dir
input_path = folder_paths.get_input_directory()
output_path = folder_paths.get_output_directory()

class CombineVideosFromFolder:
    '''
    从文件夹中合并视频，支持合并该文件夹下所有指定的相同类型的视频和音频合成为视频，并输出到指定目录
    参数：
    input_video_path: 输入视频文件夹路径
    input_audio_path: 输入音频文件夹路径
    output_path: 输出文件夹路径
    input_video_format: 输入视频格式，支持mp4、mov、avi、mkv、m4v
    input_audio_format: 输入音频格式，支持wav、mp3、m4a、flac
    output_filename: 输出文件名，不包含后缀
    output_video_format: 输出视频格式，支持mp4、mov、avi、mkv、m4v
    output_audio_format: 输出音频格式，支持wav、mp3、m4a、flac
    返回值：
    output_video_path: 输出视频文件路径
    '''

    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "input_video_path": ("STRING", {"default": ""}),
                "input_audio_path": ("STRING", {"default": ""}),
                "output_path": ("STRING", {"default": ""}),
                "input_video_format": (["mp4", "mov", "avi", "mkv", "m4v"], {"default": "mp4"}),
                "input_audio_format": (["wav", "mp3", "m4a", "flac"], {"default": "wav"}),
                "output_filename": ("STRING", {"default": "output_video"}),
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
        

class GetSubtitlesFromVideo:
    '''
    从视频中获取字幕，使用开源模型faster-whisper识别语音语言，并将语音转换为指定语言的字幕保存到指定文件夹，仅支持.srt和.vtt两种格式
    参数：
    input_file_path: 输入视频文件路径
    whisper_model: 使用的whisper模型，模型存放地址models/faster-whisper，运行节点会自动下载模型，模型下载地址为：https://huggingface.co/Systran
    device: 使用的设备，支持cpu、cuda、auto
    language: 转录的语言，auto为自动检测的原语言
    task: 转录的任务，支持transcribe和translate
    output_path: 输出文件夹路径
    output_filename: 输出文件名，不包含后缀
    output_format: 输出格式，支持srt和vtt
    返回值：
    output_subtitles_path: 输出字幕文件路径
    '''
    
    @classmethod
    def INPUT_TYPES(self):
        self.faster_whisper_model_dir = os.path.join(models_path, "faster-whisper")
        whisper_models = list(model for model in faster_whisper.available_models())
        self.whisper_models = whisper_models

        language_list = list(language for language in faster_whisper.tokenizer._LANGUAGE_CODES)
        language_list.append("auto")
        self.language_list = language_list

        return {
            "required": {
                "input_file_path": ("STRING", {"default": ""}),
                "whisper_model": (self.whisper_models, {"default": "large-v3"}),
                "device": (["cpu", "cuda", "auto"], {"default": "auto"}),
                "language": (self.language_list, {"default": "auto"}),
                "task": (["transcribe", "translate"], {"default": "transcribe"}),
                "output_path": ("STRING", {"default": ""}),
                "output_filename": ("STRING", {"default": "output_subtitles"}),
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
            
            time_str = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            output_file_path = os.path.join(output_path, f"{output_filename}_{time_str}.{output_format}")

            if language == "auto":
                language = None

            fast_whisper_model = loadAndDownloadModels(whisper_model, device, self.faster_whisper_model_dir)

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
            writeSubtitlesToFile(transcriptions, output_file_path, output_format)

            return (output_file_path,)

        except Exception as e:
            raise ValueError(f"Error: {e}")


class MergeVideoAndSubtitle:
    '''
    合并视频和字幕，将字幕显示到视频中，使用ffmpeg将字幕显示到视频中，仅支持.srt和.vtt两种格式
    参数：
    input_video_filepath: 输入视频文件路径
    input_subtitle_filepath: 输入字幕文件路径
    output_filepath: 输出文件夹路径
    output_filename: 输出文件名，不包含后缀
    output_format: 输出格式，支持mp4、mov、avi、mkv、m4v
    返回值：
    output_video_path: 输出视频文件路径
    '''

    @classmethod
    def INPUT_TYPES(self):
        return {
            "required": {
                "input_video_filepath": ("STRING", {"default": ""}),
                "input_subtitle_filepath": ("STRING", {"default": ""}),
                "output_filepath": ("STRING", {"default": ""}),
                "output_filename": ("STRING", {"default": "output_combined"}),
                "output_format": (["mp4", "mov", "avi", "mkv", "m4v"], {"default": "mp4"})
            },
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_video_path",)
    FUNCTION = "merge_video_and_subtitle"
    CATEGORY = "Combine Videos And Subtitles"
    OUTPUT_NODE = True
    
    def merge_video_and_subtitle(self, input_video_filepath, input_subtitle_filepath, output_filepath, output_filename, output_format):
        try:
            input_video_filepath = os.path.abspath(input_video_filepath).strip()
            if not check_path_exists(input_video_filepath):
                raise ValueError(f"Input video path does not exist: {input_video_filepath}")
            if not check_path_is_file(input_video_filepath):
                raise ValueError(f"Input video path is not a file: {input_video_filepath}")
            
            input_subtitle_filepath = os.path.abspath(input_subtitle_filepath).strip()
            if not check_path_exists(input_subtitle_filepath):
                raise ValueError(f"Input subtitle path does not exist: {input_subtitle_filepath}")
            if not check_path_is_file(input_subtitle_filepath):
                raise ValueError(f"Input subtitle path is not a file: {input_subtitle_filepath}")
            
            if output_filepath == "":
                raise ValueError("Output path is not inputed")
            
            if output_filename == "":
                raise ValueError("Output filename is not inputed")
            
            if output_format == "":
                raise ValueError("Output format is not selected")
            
            if check_path_is_file(output_filepath):
                raise ValueError(f"Output path is a file: {output_filepath}")
            
            if not check_path_exists(output_filepath):
                os.makedirs(output_filepath)

            time_str = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            output_video_filepath = os.path.join(output_filepath, f"{output_filename}_{time_str}.{output_format}")

            # 使用更可靠的字幕合并方法 - 避免路径解析问题
            # 将字幕文件复制到输出目录，使用相对路径
            temp_subtitle_path = os.path.join(output_filepath, "temp_subtitle.srt")
            shutil.copy2(input_subtitle_filepath, temp_subtitle_path)

            # 使用相对路径，避免Windows路径解析问题
            subtitle_filter = "subtitles=temp_subtitle.srt"
            merge_video_and_subtitle_command = ["ffmpeg", "-i", input_video_filepath, "-vf", subtitle_filter, "-c:a", "copy", output_video_filepath]

            # 切换到输出目录执行命令
            original_cwd = os.getcwd()
            os.chdir(output_filepath)

            # 执行命令...
            result = subprocess.run(merge_video_and_subtitle_command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            if result.returncode != 0:
                raise ValueError(f"Error: {result.stderr}")

            # 恢复原始工作目录
            os.chdir(original_cwd)

            # 清理临时字幕文件
            if os.path.exists(temp_subtitle_path):
                os.remove(temp_subtitle_path)

            return (output_video_filepath,)
        except Exception as e:
            raise ValueError(f"Error: {e}")



NODE_CLASS_MAPPINGS = {
    "CombineVideosFromFolder": CombineVideosFromFolder,
    "GetSubtitlesFromVideo": GetSubtitlesFromVideo,
    "MergeVideoAndSubtitle": MergeVideoAndSubtitle
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "CombineVideosFromFolder": "Combine Videos From Folder",
    "GetSubtitlesFromVideo": "Get Subtitles From Video",
    "MergeVideoAndSubtitle": "Merge Video And Subtitle"
}