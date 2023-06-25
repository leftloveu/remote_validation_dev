#!/usr/bin/python
# -*- coding: utf-8 -*-
#############################
# Function: 后台数据处理公共部分
# Author: 周若凡
# E-mail: zrfedward@gmail.com
# Date: 2023-06
# Modified by:
#   1.
#############################

import pymysql, config, math, datetime, xlwt, random, requests, os, zipfile
from flask import session
from wxcloudrun.application import application_manage_models


def json_encoder(obj):
    """提供给JSONEncoder的default方法，json将按要求序列化指定类型的对象"""
    if isinstance(obj, datetime.datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(obj, datetime.date):
        return obj.strftime("%Y-%m-%d")


# 初始化DB链接
def create_conn():
    conn = None
    try:
        conn = pymysql.connect(host=config.db_address, user=config.username, passwd=config.password, database=config.database, port=config.port, charset='utf8', cursorclass=pymysql.cursors.DictCursor)
    except Exception as e:
        print(str(e))
    return conn


def db_select(sql, keywords_dict=None):
    '''
    @function: 数据库查询公共方法
    @args:
        @sql: SQL语句
        @keywords_dict: 参数集合
    @return: 结果集合
    '''
    rows = None
    conn, cur = None, None
    try:
        conn = create_conn()
        # cursorclass = MySQLdb.cursors.DictCursor
        # 会返回一个带key的集合
        cur = conn.cursor()
        if keywords_dict:
            cur.execute(sql, keywords_dict)
        else:
            cur.execute(sql)
        rows = cur.fetchall()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        return rows


def dict_to_key_equal_symbol_array(a_dict):
    '''
    @function: 整理参数，用于拼接SQL
    @args:
        @a_dict: 参数dict
    @return: 参数SQLarray
    '''
    keys = a_dict.keys()
    array = []
    for key in keys:
        value = a_dict[key]
        if type(value) is list or type(value) is tuple:
            array.append("%s IN %%(%s)s" % (key, key))
        elif key == 'start_datetime':
            array.append("%s >= %%(%s)s" % (key, key))
        elif key == 'end_datetime':
            array.append("%s <= %%(%s)s" % (key, key))
        else:
            array.append("%s = %%(%s)s" % (key, key))
    return array


def generate_sql_by_keywords(tab_name, keywords_dict):
    '''
    @function: 用于生成SQL语句
    @args:
        @tab_name: 数据库表名
        @keywords_dict: 参数集合
    @return: SQL
    '''
    sql = "SELECT * FROM %s" % tab_name
    if len(keywords_dict) > 0:
        # if len(keywords_dict) == 2 and keywords_dict.values()[0] == keywords_dict.values()[1]:
        where_string = (" AND ").join(dict_to_key_equal_symbol_array(keywords_dict))
        # if len(keywords_dict) == 2:
        #     where_string = (" OR ").join(dict_to_key_equal_symbol_array(keywords_dict))
        # else:
        #     where_string = (" AND ").join(dict_to_key_equal_symbol_array(keywords_dict))
        sql = " WHERE ".join([sql, where_string])
    return sql


def search(tab_name, request_args, extra_args):
    '''
    @function: 用于做复杂搜索
    @args:
        @tab_name: 数据库表名
        @request_args: 请求参数集合
        @extra_args: 额外添加参数集合
    @return: 搜索后的结果集合
    '''
    final_sql = ""
    rows = {}
    total_page_size = 0
    per_page = 10
    row_count = 0
    # 如果tab_name不存在，则直接返回空
    if not tab_name or tab_name == "":
        return None, 1
    try:
        # 如果page不在extra_args， 将page初始化为1
        if 'page' not in extra_args or extra_args['page'] == None or int(extra_args['page']) == 0:
            page = 1
        else:
            page = int(extra_args['page'])

        # 如果per_page不在extra_args， 将per_page初始化为10
        if 'per_page' not in extra_args or extra_args['per_page'] == None or int(extra_args['per_page']) == 0:
            per_page = 10
        else:
            per_page = int(extra_args['per_page'])

        # Flask里request.args为immutable dict，将其转化成普通的dict。应对传入形参request_args的情况。
        keywords_dict = dict([(k, request_args[k]) for k in request_args])
        # 去除dict的空元素
        for x in list(keywords_dict.keys()):
            if keywords_dict[x] == '' or keywords_dict[x] == None:
                del keywords_dict[x]

        # 调用方法生成SQL
        sql = generate_sql_by_keywords(tab_name, keywords_dict)

        # 如果extra_where_sql在extra_args，将其拼凑到where语句当中
        if 'extra_where_sql' in extra_args and extra_args['extra_where_sql'] != '':
            if 'WHERE' in sql:
                sql += " AND " + extra_args['extra_where_sql']
            else:
                sql += " WHERE " + extra_args['extra_where_sql']

        # 如果order_sql在extra_args，将其拼凑到where语句当中
        if 'order_sql' in extra_args and extra_args['order_sql'] != '':
            sql += extra_args['order_sql']

        if page:
            final_sql = sql + " LIMIT %s OFFSET %s" % (per_page, (page - 1) * per_page)

        print(final_sql)
        print(keywords_dict)

        # 使用拼接好的SQL及参数集合，做查询
        rows = db_select(final_sql, keywords_dict)
        # 通过COUNT计算页数
        count_sql = "SELECT count(*) as count FROM (%s) as sub_rows" % (sql)
        row_count = db_select(count_sql, keywords_dict)[0]['count']
        total_page_size = int(math.ceil(row_count / float(per_page)))
    except Exception as e:
        print(str(e))
    finally:
        return rows, total_page_size, per_page, row_count

def export_search(tab_name, request_args, extra_args):
    '''
    @function: 用于做复杂搜索
    @args:
        @tab_name: 数据库表名
        @request_args: 请求参数集合
        @extra_args: 额外添加参数集合
    @return: 搜索后的结果集合
    '''
    rows = {}
    # 如果tab_name不存在，则直接返回空
    if not tab_name or tab_name == "":
        return None, 1
    try:
        # Flask里request.args为immutable dict，将其转化成普通的dict。应对传入形参request_args的情况。
        keywords_dict = dict([(k, request_args[k]) for k in request_args])
        # 去除dict的空元素
        for x in list(keywords_dict.keys()):
            if keywords_dict[x] == '' or keywords_dict[x] == None:
                del keywords_dict[x]

        # 调用方法生成SQL
        sql = generate_sql_by_keywords(tab_name, keywords_dict)

        # 如果extra_where_sql在extra_args，将其拼凑到where语句当中
        if 'extra_where_sql' in extra_args and extra_args['extra_where_sql'] != '':
            if 'WHERE' in sql:
                sql += " AND " + extra_args['extra_where_sql']
            else:
                sql += " WHERE " + extra_args['extra_where_sql']

        # 如果order_sql在extra_args，将其拼凑到where语句当中
        if 'order_sql' in extra_args and extra_args['order_sql'] != '':
            sql += extra_args['order_sql']

        print(sql)
        print(keywords_dict)

        # 使用拼接好的SQL及参数集合，做查询
        rows = db_select(sql, keywords_dict)
    except Exception as e:
        print(str(e))
    finally:
        return rows


def generate_data_file(application_list_export):
    upload_file_name_with_url_code_list = [
        {'url_code': 'id_files/id_file', 'file_name': '运输车辆司机身份证', 'suffix': '.jpg'},
        {'url_code': 'driver_license_files/driver_license_file', 'file_name': '运输车辆司机驾驶证', 'suffix': '.jpg'},
        {'url_code': 'vehicle_license_files/vehicle_license_file', 'file_name': '运输车辆行驶证', 'suffix': '.jpg'},
        {'url_code': 'over_limit_license_files/over_limit_license_file', 'file_name': '运输车辆超限运输证', 'suffix': '.jpg'},
        {'url_code': 'road_operating_license_files/road_operating_license_file', 'file_name': '运输车辆道路经营许可证', 'suffix': '.jpg'},
        {'url_code': 'solution_files/solution_file', 'file_name': '护送方案文件', 'suffix': '.pdf'},
        {'url_code': 'escort_solution_files/escort_solution_file', 'file_name': '护送方案照片', 'suffix': '.jpg'},
        {'url_code': 'escort_driver_license_files/escort_driver_license_file', 'file_name': '护送车辆司机驾驶证', 'suffix': '.jpg'},
        {'url_code': 'escort_vehicle_license_files/escort_vehicle_license_file', 'file_name': '护送车辆行驶证', 'suffix': '.jpg'},
        {'url_code': 'escort_vehicle_files/escort_vehicle_file', 'file_name': '护送车辆照片', 'suffix': '.jpg'},
        {'url_code': 'valid_vehicle_left_front_files/valid_vehicle_left_front_file', 'file_name': '现场验证照片_左前方', 'suffix': '.jpg'},
        {'url_code': 'valid_vehicle_front_files/valid_vehicle_front_file', 'file_name': '现场验证照片_正前方', 'suffix': '.jpg'},
        {'url_code': 'valid_vehicle_right_front_files/valid_vehicle_right_front_file', 'file_name': '现场验证照片_右前方', 'suffix': '.jpg'},
        {'url_code': 'valid_vehicle_left_back_files/valid_vehicle_left_back_file', 'file_name': '现场验证照片_左后方', 'suffix': '.jpg'},
        {'url_code': 'valid_vehicle_back_files/valid_vehicle_back_file', 'file_name': '现场验证照片_正后方', 'suffix': '.jpg'},
        {'url_code': 'valid_vehicle_right_back_files/valid_vehicle_right_back_file', 'file_name': '现场验证照片_右后方', 'suffix': '.jpg'},
        {'url_code': 'valid_whole_scene', 'file_name': '现场验证照片_全景照片', 'suffix': '.jpg'},
    ]


    # 生成excel， 下载资料（图片+文件），压缩
    data_export_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    data_export_random_num = random.randint(10000, 99999)

    _dir = os.path.dirname(os.path.abspath(__file__))
    _updir = os.path.abspath(os.path.join(_dir, '..'))
    _path = _updir + '/static/temp_files/'

    # 创建资料导出的根目录:file_export_path
    # server：/app/wxcloudrun/static/temp_files/data_export_{用户名}_202306251200101234_88888/
    # local：/Users/zhouruofan/Documents/00-Work/49-自研/00-重庆交通运输执法/01-测试小程序/remote_validation_dev/wxcloudrun/static/temp_files/data_export_{用户名}_202306251200101234_88888/
    data_export_dir_name = 'data_export_' + str(session['user_info']['user_name']) + "_" + str(data_export_timestamp) + "_" + str(data_export_random_num) + "/"
    file_export_path = _path + data_export_dir_name

    if not os.path.exists(file_export_path):
        os.mkdir(file_export_path)

    # step_1: 生成excel
    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet(u'申报单明细')
    font = xlwt.Font()  # Create Font
    font.bold = True  # Set font to Bold
    style = xlwt.XFStyle()  # Create Style
    style.font = font  # Add Bold Font to Style
    row = 0
    heads = [
        u"申报单号",
        u"申报单状态",
        u"审核意见",
        u"检查时间",
        u"牵引车车牌",
        u"挂车车牌",
        u"通行开始时间",
        u"通行结束时间",
        u"审批路线",
        u"车属单位",
        u"护送方案是否一致",
        u"经办人",
        u"检查收费站",
        u"通行证号",
        u"实际通行时间",
        u"实际线路",
        u"承运单位",
        u"监护车车牌号",
        u"共运车次",
        u"联系方式",
        u"其他情况",
    ]
    for i in range(len(heads)):
        worksheet.write(row, i, heads[i], style)

    for application in application_list_export:
        if application["apply_order_status"] == 0:
            application["apply_order_status"] = u'草稿'
        elif application["apply_order_status"] == 1:
            application["apply_order_status"] = u'拟验证'
        elif application["apply_order_status"] == 2:
            application["apply_order_status"] = u'验证中'
        elif application["apply_order_status"] == 3:
            application["apply_order_status"] = u'验证通过'
        elif application["apply_order_status"] == 4:
            application["apply_order_status"] = u'验证不通过'
        elif application["apply_order_status"] == 5:
            application["apply_order_status"] = u'已取消'

        if application["escort_plate_number_2"]:
            escort_plate_number_str = application['escort_plate_number_1'] + ", " + application['escort_plate_number_2']
        else:
            escort_plate_number_str = application['escort_plate_number_1']

        row += 1
        worksheet.write(row, 0, application["apply_order_num"] if application["apply_order_num"] else '')
        worksheet.write(row, 1, application["apply_order_status"] if application["apply_order_status"] else '')
        worksheet.write(row, 2, application["adjust_comment"] if application["adjust_comment"] else '')
        worksheet.write(row, 3, application["verification_datetime"].strftime("%Y-%m-%d %H:%M:%S") if application["verification_datetime"] else '')
        worksheet.write(row, 4, application["plate_number"] if application["plate_number"] else '')
        # worksheet.write(row, 5, '')
        worksheet.write(row, 6, application["start_datetime"].strftime("%Y-%m-%d %H:%M:%S") if application["start_datetime"] else '')
        worksheet.write(row, 7, application["end_datetime"].strftime("%Y-%m-%d %H:%M:%S") if application["end_datetime"] else '')
        worksheet.write(row, 8, application["approved_path"] if application["approved_path"] else '')
        worksheet.write(row, 9, application['vehicle_department'] if application["vehicle_department"] else '')
        # worksheet.write(row, 10, '')
        worksheet.write(row, 11, application['verification_officer_name'] if application["verification_officer_name"] else '')
        worksheet.write(row, 12, application['appoint_verification_location'] if application["appoint_verification_location"] else '')
        # worksheet.write(row, 13, '')
        # worksheet.write(row, 14, '')
        worksheet.write(row, 15, application['approved_path'] if application["approved_path"] else '')
        worksheet.write(row, 16, application['charge_department'] if application["charge_department"] else '')
        worksheet.write(row, 17, escort_plate_number_str if escort_plate_number_str else '')
        worksheet.write(row, 18, application['plate_transport_time'] if application["plate_transport_time"] else '')
        worksheet.write(row, 19, application['driver_mobile_number'] if application["driver_mobile_number"] else '')
        # worksheet.write(row, 20, '')

    data_export_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    data_export_random_num = random.randint(10000, 99999)

    data_file_name = u"application_export" + "_" + str(session['user_info']['user_name']) + "_" + str(data_export_timestamp) + "_" + str(data_export_random_num) + ".xls"
    data_file_path = file_export_path + data_file_name

    print(data_file_path)
    workbook.save(data_file_path)

    # step_2: 下载资料（图片+文件）
    # 遍历application_list_export获取apply_order_num，基于apply_order_num获取相关资料文件
    for application in application_list_export:
        # 在导出资料的根目录下，每张申报单都创建一个目录
        upload_file_dir_name = str(application['apply_order_num']) + "/"
        upload_file_export_path = file_export_path + upload_file_dir_name

        if not os.path.exists(upload_file_export_path):
            os.mkdir(upload_file_export_path)

        wx_download_file_url_list = []
        wx_download_file_object = application_manage_models.get_files_list_by_apply_order_num(application['apply_order_num'])

        if 'errcode' in wx_download_file_object.keys() and wx_download_file_object['errcode'] == 0:
            wx_download_file_list = wx_download_file_object['file_list']
            for item in wx_download_file_list:
                if 'download_url' in item.keys():
                    wx_download_file_url_list.append(item['download_url'])
            wx_download_file_url_list.sort()

            # 将文件保存到本地
            for wx_download_file_url in wx_download_file_url_list:
                for file_name_with_url_code in upload_file_name_with_url_code_list:
                    if file_name_with_url_code['url_code'] in wx_download_file_url:
                        data_export_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
                        data_export_random_num = random.randint(10000, 99999)

                        upload_file_name = application['apply_order_num'] + "_" + str(file_name_with_url_code['file_name']) + "_" + str(data_export_timestamp) + "_" + str(data_export_random_num) + str(file_name_with_url_code['suffix'])
                        upload_file_path = upload_file_export_path + upload_file_name
                        print(upload_file_path)
                        resp = requests.get(wx_download_file_url)
                        with open(upload_file_path, "wb") as f:
                            f.write(resp.content)
    # step_3: 压缩
    # file_export_path = /Users/zhouruofan/Documents/00-Work/49-自研/00-重庆交通运输执法/01-测试小程序/remote_validation_dev/wxcloudrun/static/temp_files/data_export_周若凡-执法_20230625203621938341_64302/
    zipfile_output_fullname = file_export_path[:-1] + ".zip"
    zip = zipfile.ZipFile(zipfile_output_fullname, "w", zipfile.ZIP_DEFLATED)
    for path, dirnames, filenames in os.walk(file_export_path):
        fpath = path.replace(file_export_path, '')
        for filename in filenames:
            zip.write(os.path.join(path, filename), os.path.join(fpath, filename))
    zip.close()
    # step_4: 删除原始文件
    for root, dirs, files in os.walk(file_export_path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))

    data_export_zipfile_absolute_path = '/static/temp_files/' + data_export_dir_name[:-1] + ".zip"

    print(data_export_zipfile_absolute_path)

    return data_export_zipfile_absolute_path

def db_select_pagination(sql, keywords_dict=None):
    '''
    @function: 数据库查询公共方法
    @args:
        @sql: SQL语句
        @keywords_dict: 参数集合
    @return: 结果集合
    '''
    rows = None
    conn, cur = None, None
    page_num = 1
    page_size = 3
    total_page_size = 0
    try:
        conn = create_conn()
        # cursorclass = MySQLdb.cursors.DictCursor
        # 会返回一个带key的集合
        cur = conn.cursor()
        '''
        分页查询数据, 默认第1页,20条数据
        :param page_num:  页数
        :param page_size: 每页的数据行数
        :return:
        '''
        limit = "LIMIT %d,%d" % ((int(page_num) - int(1)) * int(page_size), page_size)
        sql = "SELECT t.*,t1.classroom_name FROM t_c_seat t LEFT JOIN " \
              "t_c_classroom t1 ON " \
              "t.classroom_id = t1.classroom_id where 1=1 "

        limit_sql = sql + limit

        cur.execute(limit_sql)
        rows = cur.fetchall()

        count_sql = "SELECT count(*) as count FROM (%s) as sub_rows" % (sql)

        row_count = db_select(count_sql)[0]['count']
        total_page_size = int(math.ceil(row_count / float(page_size)))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
        return rows, total_page_size
