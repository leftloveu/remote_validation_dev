#!/usr/bin/python
# -*- coding: utf-8 -*-
#############################
# Function: 申报单后台数据处理
# Author: 周若凡
# E-mail: zrfedward@gmail.com
# Date: 2023-06
# Modified by:
#   1.
#############################

import os, sys, json, requests
import pymysql
import config

_dir = os.path.dirname(os.path.abspath(__file__))
_updir = os.path.abspath(os.path.join(_dir, '..'))
if _updir not in sys.path:
    sys.path.insert(0, _updir)

from flask import session, g
from wxcloudrun.common import common_models


def get_files_list_by_apply_order_num(apply_order_num):
    wx_batchDownloadFile_request_url = 'http://api.weixin.qq.com/tcb/batchdownloadfile'
    wx_batchDownloadFile_request_params = {
        'env': 'prod-1g5rodur3c83b6f2'
    }
    cloudID_item = {}
    file_list = []
    wx_download_file_object = {}
    conn, cursor = None, None
    try:
        conn = common_models.create_conn()
        cursor = conn.cursor()
        # step 1: 基于apply_order_num获取cloudID
        sql = [
            " SELECT  ",
            " application.* ",
            ",valid_photo.* ",
            " FROM t_a_application application, ",
            " t_a_application_valid_photo valid_photo ",
            " WHERE application.apply_order_num = %s " % apply_order_num,
            " AND application.apply_order_num = valid_photo.apply_order_num "
        ]
        cursor.execute("".join(sql))
        row = cursor.fetchone()
        if row and len(row) > 0:
            # step 2: 基于cloudID获取文件url
            for key in (row.keys()):
                if 'cloudID' in key and row[key] is not None:
                    if "||" in row[key]:
                        cloudID_list = row[key].split("||")
                        for cloudID in cloudID_list:
                            cloudID_item = {
                                "fileid": cloudID,
                                "max_age": 7200
                            }
                            file_list.append(cloudID_item)
                    else:
                        cloudID_item = {
                            "fileid": row[key],
                            "max_age": 7200
                        }
                        file_list.append(cloudID_item)
            wx_batchDownloadFile_request_params['file_list'] = file_list

            result = requests.post(wx_batchDownloadFile_request_url, data=json.dumps(wx_batchDownloadFile_request_params))
            wx_download_file_object = json.loads(result.content)
            print('------ application_manage_models wx_download_file_object %s' % apply_order_num)
            print(wx_download_file_object)
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return wx_download_file_object
