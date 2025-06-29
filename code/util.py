import os
import json
import zipfile
from PIL import Image
import cv2
import numpy as np
import io
import base64
import database
import subprocess
from datetime import datetime
from PIL import Image
from io import BytesIO
from core import DataParserFactory
import parsers.registry

def identify_data_type(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".svg"]:
        return "CommonImage"
    elif ext in [".tif", ".tiff"]:
        return "GeoTIFFImage"
    elif ext in [".hdr", ".raw", ".img"]:
        return "EnviImage/ERDASImage"
    elif ext in ['.mp4', '.mkv', '.mov', '.avi', '.wmv', '.flv', '.webm', '.mpeg', '.mpg', '.3gp', '.ts', '.m4v']:
        return "CommonVideo"
    elif ext in [".hdf", ".hdf5", ".he5"]:
        return "HDF5"
    elif ext in [".nc"]:
        return "NetCDF"
    # elif ext in [".las", ".laz"]:
    #     return "pointcloud"
    # elif ext == ".json":
    #     return "metadata"
    # elif ext == ".vtk":
    #     return "visualization"
    else:
        return "unknown"

def process_file(file_path):
    try:
        parser = DataParserFactory.get_parser(file_path)
        metadata = parser.parse(file_path)
        return metadata
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

def get_and_unzip_zip_file(sql_dirt):
    #从给定路径获取ZIP文件
    if not os.path.exists(sql_dirt['save_path']):
        raise FileNotFoundError(f"文件 {sql_dirt['save_path']} 不存在")
    if not sql_dirt['save_path'].endswith('.zip'):
        raise ValueError(f"文件 {sql_dirt['save_path']} 不是ZIP文件")
    
    #解压ZIP文件到指定目录
    if not os.path.exists(sql_dirt['uri']):
        os.makedirs(sql_dirt['uri'])
    
    with zipfile.ZipFile(sql_dirt['save_path'], 'r') as zip_ref:
        zip_ref.extractall(sql_dirt['uri'])

def extract_zip_file(sql_dirt):
    total_num = 0
    extract_num = 0

    if sql_dirt["data_type"] == 3:
        valid_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".svg", ".tif", ".tiff", ".envi", ".hdr", ".raw", ".img")

        output_dir = os.path.dirname(sql_dirt["conver_file_uri"])
        fail_dir = os.path.dirname(sql_dirt["fail_uri"])
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        if not os.path.exists(fail_dir):
            os.makedirs(fail_dir)

        if not os.path.exists(sql_dirt["conver_file_uri"]):
            with open(sql_dirt["conver_file_uri"], 'w') as f:
                json.dump([], f)
        if not os.path.exists(sql_dirt["fail_uri"]):
            with open(sql_dirt["fail_uri"], 'w') as f:
                json.dump([], f)

        with open(sql_dirt["conver_file_uri"], 'r') as f:
            output_list = json.load(f)
        with open(sql_dirt["fail_uri"], 'r') as f:
            fail_list = json.load(f)

        for root, dirs, files in os.walk(sql_dirt['uri']):
            for filename in files:
                file_path = os.path.join(root, filename)
                if filename.lower().endswith(valid_extensions):
                    dirt = process_file(file_path)
                    if dirt is not None:
                        sql_file_dirt = {
                            "name": filename,
                            "status": 0,
                            "dataset_id": sql_dirt["id"],
                            "file_url": os.path.join(sql_dirt['uri'], filename),
                            "create_user_id": sql_dirt["create_user_id"],
                            "create_time": datetime.now(),
                            "file_type": os.path.splitext(filename)[-1][1:].lower()
                        }
                        output_list.append(dirt)
                        database.insert_data_file_n(sql_file_dirt)
                        extract_num += 1
                    else:
                        dirt = {"filename": filename}
                        fail_list.append(dirt)
                else:
                    dirt = {"filename": filename}
                    fail_list.append(dirt)
                total_num += 1
        try:
            with open(sql_dirt["conver_file_uri"], 'w') as f:
                json.dump(output_list, f, indent=4)
            with open(sql_dirt["fail_uri"], 'w') as f:
                json.dump(fail_list, f, indent=4)
        except Exception as e:
            print(f"处理文件时出错: {e}")
    elif sql_dirt["data_type"] == 4:
        valid_extensions = ('.mp4', '.mkv', '.mov', '.avi', '.wmv', '.flv', '.webm', '.mpeg', '.mpg', '.3gp', '.ts', '.m4v')

        output_dir = os.path.dirname(sql_dirt["conver_file_uri"])
        fail_dir = os.path.dirname(sql_dirt["fail_uri"])
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        if not os.path.exists(fail_dir):
            os.makedirs(fail_dir)

        if not os.path.exists(sql_dirt["conver_file_uri"]):
            with open(sql_dirt["conver_file_uri"], 'w') as f:
                json.dump([], f)
        if not os.path.exists(sql_dirt["fail_uri"]):
            with open(sql_dirt["fail_uri"], 'w') as f:
                json.dump([], f)

        with open(sql_dirt["conver_file_uri"], 'r') as f:
            output_list = json.load(f)
        with open(sql_dirt["fail_uri"], 'r') as f:
            fail_list = json.load(f)

        for root, dirs, files in os.walk(sql_dirt['uri']):
            for filename in files:
                file_path = os.path.join(root, filename)
                if filename.lower().endswith(valid_extensions):
                    dirt = process_file(file_path)
                    if dirt is not None:
                        sql_file_dirt = {
                            "name": filename,
                            "status": 0,
                            "dataset_id": sql_dirt["id"],
                            "file_url": os.path.join(sql_dirt['uri'], filename),
                            "create_user_id": sql_dirt["create_user_id"],
                            "create_time": datetime.now(),
                            "file_type": os.path.splitext(filename)[-1][1:].lower()
                        }
                        output_list.append(dirt)
                        database.insert_data_file_n(sql_file_dirt)
                        extract_num += 1
                    else:
                        dirt = {"filename": filename}
                        fail_list.append(dirt)
                else:
                    dirt = {"filename": filename}
                    fail_list.append(dirt)
                total_num += 1
        try:
            with open(sql_dirt["conver_file_uri"], 'w') as f:
                json.dump(output_list, f, indent=4)
            with open(sql_dirt["fail_uri"], 'w') as f:
                json.dump(fail_list, f, indent=4)
        except Exception as e:
            print(f"处理文件时出错: {e}")

    return 1, extract_num, total_num

def process_zip_file(sql_dirt):
    extract_num = 0 
    total_num = 0
    flag = 1
    sql_dirt['uri'] = os.path.join(sql_dirt['uri'], str(sql_dirt['id']))
    try:
        # 读取与解压
        get_and_unzip_zip_file(sql_dirt)
        flag, extract_num, total_num = extract_zip_file(sql_dirt)
    except Exception as e:
        print(f"处理文件时出错: {e}")
        flag = 0
    
    print(extract_num, total_num)

    # 解压成功并更改sql
    sql_dirt["update_time"] = datetime.now()
    sql_dirt["status"] = 2 if flag == 1 else 3
    sql_dirt["data_size"] = extract_num
    sql_dirt["data_src_size"] = total_num

    database.update_data_dataset_n(sql_dirt)