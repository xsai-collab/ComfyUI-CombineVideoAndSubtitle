import os
import glob

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

# 获取指定路径下的所有文件
def get_files(path, file_format):
    files = []
    for file in glob.glob(os.path.join(path, f"*.{file_format}")):
        files.extend(file)

    files.sort()
    return files

# 获取文件名
def get_file_name(path):
    return os.path.basename(path)
