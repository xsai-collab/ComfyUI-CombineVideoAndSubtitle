import os
import glob
import faster_whisper

# 检查路径是否存在
def check_path_exists(path):
    if not os.path.exists(path):
        return False
    return True

# 检查路径是否为目录
def check_path_is_dir(path):
    if not os.path.isdir(path):
        return False
    return True

# 检查路径是否为文件
def check_path_is_file(path):
    if not os.path.isfile(path):
        return False
    return True

# 获取指定路径下的所有文件
def get_files(path, file_format):
    files = []
    files.extend(glob.glob(os.path.join(path, f"*.{file_format}")))
    files.sort()
    return files

# 获取文件名
def get_file_name(path):
    return os.path.basename(path)


# 加载模型
def loadAndDownloadModels(whisper_model, device, download_root) -> faster_whisper.WhisperModel:
    if not check_path_exists(download_root):
        os.makedirs(download_root)
    fast_whisper_model = faster_whisper.WhisperModel(
        model_size_or_path=whisper_model,
        device=device,
        download_root=download_root,
        local_files_only=False
    )
    return fast_whisper_model
    
# 将字幕写入文件
def writeSubtitlesToFile(subtitles, output_file_path, output_format):
    subtitle_text = ""
    if output_format == "srt":
        start_text = ""
    elif output_format == "vtt":
        start_text = "WEBVTT\n\n"

    subtitle_text += start_text

    for i, subtitle in enumerate(subtitles):
        start_time = format_time(subtitle["start"], output_format)
        end_time = format_time(subtitle["end"], output_format)
        text = subtitle["text"].strip()

        subtitle_text += f"{i+1}\n"
        subtitle_text += f"{start_time} --> {end_time}\n"
        subtitle_text += f"{text}\n\n"
        
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(subtitle_text)

# 格式化时间
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