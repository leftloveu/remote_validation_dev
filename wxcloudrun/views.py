from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from sqlalchemy.exc import OperationalError
from wxcloudrun import db
import pymysql
import config
import random
pymysql.install_as_MySQLdb()
import json
import logging
import requests, time, hashlib

# 初始化日志
# logger = logging.getLogger('log')


# 初始化DB链接
def create_conn():
    conn = None
    try:
        conn = pymysql.connect(host=config.db_address, user=config.username, passwd=config.password, database=config.database, port=config.port, charset='utf8', cursorclass=pymysql.cursors.DictCursor)
    except Exception as e:
        print(str(e))
    return conn


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return make_succ_response('index.html')

@app.route('/api/test', methods=['GET'])
def test():
    return make_succ_response('this is a test API1')

@app.route('/api/check_user_status', methods=['POST'])
def check_user_status():
    print('/api/check_user_status')
    conn = None
    cursor = None
    user_info = ''
    try:
        print('check_user_status start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 检查openid参数
        if 'openid' not in params:
            return make_err_response('缺少openid参数')
        # openid存在，开始校验此openid是否绑定角色
        # 获取游标
        cursor = conn.cursor()
        sql = (
            " select * ",
            " from ",
            " t_u_user ",
            " where ",
            " user_openid = '%s'" % params['openid']
        )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        row = cursor.fetchone()
        print(row)
        if row:
            user_info = row
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return user_info

@app.route('/api/bind_driver_info', methods=['POST'])
def bind_driver_info():
    conn = None
    cursor = None
    result = 'false'
    try:
        print('bind_driver_info start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 获取游标
        cursor = conn.cursor()
        sql = (
            "INSERT INTO t_u_user (",
                "user_name, ",
                "user_id_card_num, ",
                "user_mobile, ",
                "user_openid, ",
                "user_role ",
            ") VALUE ( ",
                "%(user_name)s, ",
                "%(user_id_card_num)s, ",
                "%(user_mobile)s, ",
                "%(user_openid)s, ",
                "%(user_role)s) "
        )
        args = {
            'user_name': params['name'],
            'user_id_card_num': params['idcard'],
            'user_mobile': params['mobile'],
            'user_openid': params['openid'],
            'user_role': params['role']
        }
        print(" ".join(sql))
        cursor.execute(" ".join(sql), args)
        conn.commit()
        result = 'true'
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return result

@app.route('/api/modify_driver_info', methods=['POST'])
def modify_driver_info():
    conn = None
    cursor = None
    result = 'false'
    try:
        print('modify_driver_info start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 获取游标
        cursor = conn.cursor()
        sql = (
            "UPDATE t_u_user SET ",
            "user_name = '%s', " % params['user_name'],
            "user_mobile = '%s', " % params['user_mobile'],
            "user_id_card_num = '%s' " % params['user_id_card_num'],
            "WHERE ",
            "user_openid = '%s' " % params['openid']
            )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        conn.commit()
        result = 'true'
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return result

@app.route('/api/bind_officer_info', methods=['POST'])
def bind_officer_info():
    conn = None
    cursor = None
    result = 'false'
    try:
        print('bind_officer_info start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 获取游标
        cursor = conn.cursor()
        sql = [
            "UPDATE t_u_user SET ",
            "user_openid = '%s' " % params['openid'],
            "WHERE user_mobile = '%s' " % params['user_mobile'],
            "AND user_role = '%s' " % params['role']
        ]
        print("".join(sql))
        cursor.execute("".join(sql))
        conn.commit()
        result = 'true'
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return result

@app.route('/api/get_apply_info_list', methods=['POST'])
def get_apply_info_list():
    conn = None
    cursor = None
    apply_info = ''
    try:
        print('get_apply_info_list start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 检查openid参数
        if 'openid' not in params:
            return make_err_response('缺少openid参数')
        # openid存在，开始校验此openid是否绑定角色
        # 获取游标
        cursor = conn.cursor()
        sql = (
            " select apply_order_id",
            ",apply_order_num ",
            ",DATE_FORMAT(apply_order_create_time, '%Y-%m-%d %H:%i:%S') AS apply_order_create_time ",
            ",DATE_FORMAT(apply_order_submit_time,'%Y-%m-%d %H:%i:%S') as apply_order_submit_time ",
            ",plate_number ",
            ",approved_path ",
            ",appoint_verification_location ",
            ",apply_order_status ",
            ",adjust_comment ",
            ",verification_officer_name ",
            " from ",
            " t_a_application ",
            " where ",
            " apply_order_submit_openid = '%s'" % params['openid'],
            " order by ",
            " apply_order_create_time DESC ",
            ",apply_order_submit_time desc "
        )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        rows = cursor.fetchall()
        print(rows)
        if rows:
            apply_info = rows
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return make_succ_response(apply_info)

@app.route('/api/cancel_apply', methods=['POST'])
def cancel_apply():
    conn = None
    cursor = None
    result = 'false'
    try:
        print('cancel_apply start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 检查openid参数
        if 'apply_order_num' not in params:
            return make_err_response('缺少apply_order_num参数')
        # openid存在，开始校验此openid是否绑定角色
        # 获取游标
        cursor = conn.cursor()
        sql = (
            " update t_a_application ",
            " set apply_order_status = 5 ",
            " where apply_order_num = '%s' " %  params['apply_order_num']
        )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        conn.commit()
        result = 'true'
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return result

@app.route('/api/get_apply_info_list_officer', methods=['POST'])
def get_apply_info_list_officer():
    conn = None
    cursor = None
    apply_info_officer = ''
    try:
        print('get_apply_info_list_officer start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 检查openid参数
        if 'openid' not in params:
            return make_err_response('缺少openid参数')
        # openid存在，开始校验此openid是否绑定角色
        # 获取游标
        cursor = conn.cursor()
        # 如果是一支队的账号，则查全部
        sql_check = (
            " select user_associated_account ",
            " from ",
            " t_u_user ",
            " where ",
            " user_openid = '%s'" % params['openid'],
            " and ",
            " user_associated_account = 'YZDZHZX' "
        )
        cursor.execute(" ".join(sql_check))
        rows = cursor.fetchall()
        if len(rows) > 0:
            # 当前openid绑定的账号是一支队的账号
            sql = (
                " select d.apply_order_id",
                ",d.apply_order_num ",
                ",DATE_FORMAT(d.apply_order_create_time, '%Y-%m-%d %H:%i:%S') AS apply_order_create_time",
                ",DATE_FORMAT(d.apply_order_submit_time,'%Y-%m-%d %H:%i:%S') as apply_order_submit_time ",
                ",d.plate_number ",
                ",d.approved_path ",
                ",d.appoint_verification_location ",
                ",d.apply_order_status ",
                ",d.verification_officer_name ",
                ",d.adjust_comment ",
                " FROM ",
                " t_a_application d ",
                # " where d.apply_order_status = 1 ",
                " order by apply_order_submit_time desc "
            )
        else:
            sql = (
                " select d.apply_order_id",
                ",d.apply_order_num ",
                ",DATE_FORMAT(d.apply_order_create_time, '%Y-%m-%d %H:%i:%S') AS apply_order_create_time",
                ",DATE_FORMAT(d.apply_order_submit_time,'%Y-%m-%d %H:%i:%S') as apply_order_submit_time ",
                ",d.plate_number ",
                ",d.approved_path ",
                ",d.appoint_verification_location ",
                ",d.apply_order_status ",
                ",d.verification_officer_name ",
                ",d.adjust_comment ",
                "FROM ",
                "t_a_application d ",
                "WHERE d.toll_station_id ",
                "IN ( SELECT c.toll_station_id ",
                "FROM ",
                "t_u_user a, ",
                "t_u_office_account b, ",
                "t_t_toll_station c ",
                "WHERE ",
                "a.user_openid = '%s'" % params['openid'],
                "AND a.user_associated_account = b.office_account ",
                "AND b.office_id = c.office_id) ",
                # "AND d.apply_order_status = 1 ",
                "order by apply_order_submit_time desc "
            )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        rows = cursor.fetchall()
        print(rows)
        if rows:
            apply_info_officer = rows
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return make_succ_response(apply_info_officer)

@app.route('/api/get_valid_info_list_officer', methods=['POST'])
def get_valid_info_list_officer():
    conn = None
    cursor = None
    apply_info_officer = ''
    try:
        print('get_valid_info_list_officer start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 检查openid参数
        if 'openid' not in params:
            return make_err_response('缺少openid参数')
        # openid存在，开始校验此openid是否绑定角色
        # 获取游标
        cursor = conn.cursor()
        sql = (
            " select d.apply_order_id",
            ",d.apply_order_num ",
            ",DATE_FORMAT(d.apply_order_submit_time,'%Y-%m-%d %H:%i:%S') as apply_order_submit_time ",
            ",d.plate_number ",
            ",d.approved_path ",
            ",d.appoint_verification_location ",
            ",d.apply_order_status ",
            "FROM ",
            "t_a_application d ",
            "WHERE d.toll_station_id ",
            "IN ( SELECT c.toll_station_id ",
            "FROM ",
            "t_u_user a, ",
            "t_u_office_account b, ",
            "t_t_toll_station c ",
            "WHERE ",
            "a.user_openid = '%s'" % params['openid'],
            "AND a.user_associated_account = b.office_account ",
            "AND b.office_id = c.office_id) ",
            # "AND d.apply_order_status = 2 ",
            "order by d.apply_order_submit_time desc "
        )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        rows = cursor.fetchall()
        print(rows)
        if rows:
            apply_info_officer = rows
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return make_succ_response(apply_info_officer)

@app.route('/api/get_valid_info_list', methods=['POST'])
def get_valid_info_list():
    conn = None
    cursor = None
    apply_info = ''
    try:
        print('get_valid_info_list start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 检查openid参数
        if 'openid' not in params:
            return make_err_response('缺少openid参数')
        # openid存在，开始校验此openid是否绑定角色
        # 获取游标
        cursor = conn.cursor()
        sql = (
            " select apply_order_id",
            ",apply_order_num ",
            ",DATE_FORMAT(apply_order_submit_time,'%Y-%m-%d %H:%i:%S') as apply_order_submit_time ",
            ",plate_number ",
            ",approved_path ",
            ",appoint_verification_location ",
            ",apply_order_status ",
            " from ",
            " t_a_application ",
            " where ",
            " apply_order_submit_openid = '%s'" % params['openid'],
            " AND apply_order_status in (1, 2) "
            " order by apply_order_submit_time desc "
        )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        rows = cursor.fetchall()
        print(rows)
        if rows:
            apply_info = rows
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return make_succ_response(apply_info)

@app.route('/api/get_qrcode_by_apply_order_num', methods=['POST'])
def get_qrcode_by_apply_order_num():
    conn = None
    cursor = None
    driver_verified_apply_list = ''
    try:
        print('get_qrcode_by_apply_order_num start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 检查openid参数
        if 'apply_order_num' not in params:
            return make_err_response('缺少apply_order_num参数')
        # openid存在，开始校验此openid是否绑定角色
        # 获取游标
        cursor = conn.cursor()
        sql = (
            " select apply_order_id ",
            ",apply_order_num ",
            ",DATE_FORMAT(apply_order_submit_time,'%Y-%m-%d %H:%i:%S') as apply_order_submit_time ",
            ",DATE_FORMAT(start_datetime,'%Y-%m-%d %H:%i') as start_datetime ",
            ",DATE_FORMAT(end_datetime,'%Y-%m-%d %H:%i') as end_datetime ",
            ",plate_number ",
            ",approved_path ",
            ",appoint_verification_location ",
            ",apply_order_status ",
            " from ",
            " t_a_application ",
            " where ",
            " apply_order_num = '%s' " % params['apply_order_num'],
        )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        row = cursor.fetchone()
        print(row)
        if row:
            driver_verified_apply_list = row
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return make_succ_response(driver_verified_apply_list)

@app.route('/api/get_driver_verified_apply', methods=['POST'])
def get_driver_verified_apply():
    conn = None
    cursor = None
    driver_verified_apply_list = ''
    try:
        print('get_driver_verified_apply start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 检查openid参数
        if 'openid' not in params:
            return make_err_response('缺少openid参数')
        # openid存在，开始校验此openid是否绑定角色
        # 获取游标
        cursor = conn.cursor()
        sql = (
            " select apply_order_id ",
            ",apply_order_num ",
            ",DATE_FORMAT(apply_order_submit_time,'%Y-%m-%d %H:%i:%S') as apply_order_submit_time ",
            # ",DATE_FORMAT(start_date,'%Y-%m-%d') as start_date ",
            # ",DATE_FORMAT(start_time,'%H:%i:%S') as start_time ",
            # ",DATE_FORMAT(end_date,'%Y-%m-%d') as end_date ",
            # ",DATE_FORMAT(end_time,'%H:%i:%S') as end_time ",
            ",DATE_FORMAT(start_datetime,'%Y-%m-%d %H:%i') as start_datetime ",
            ",DATE_FORMAT(end_datetime,'%Y-%m-%d %H:%i') as end_datetime ",
            ",plate_number ",
            ",approved_path ",
            ",appoint_verification_location ",
            ",apply_order_status ",
            " from ",
            " t_a_application ",
            " where ",
            " apply_order_submit_openid = '%s' " % params['openid'],
            " AND apply_order_status in (3,4) ",
            # " AND now() >= start_datetime ",
            # " AND now() <= end_datetime ",
            " order by apply_order_create_time desc "
        )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        row = cursor.fetchone()
        print(row)
        if row:
            driver_verified_apply_list = row
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return make_succ_response(driver_verified_apply_list)

@app.route('/api/new_apply', methods=['POST'])
def new_apply():
    conn = None
    cursor = None
    result = 'false'
    final_sql = ''
    try:
        print('new_apply start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 向params追加其他参数
        # params['apply_order_num'] = datetime.now().strftime("%Y%m%d%H%M%S%f") + str(random.randint(10000, 99999))
        params['apply_order_status'] = 0 # 草稿
        params['apply_order_create_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 获取游标
        cursor = conn.cursor()
        # 按数据包的key-value拼接SQL
        sql_1_list = ["INSERT INTO t_a_application ("]
        for key in params.keys():
            sql_1_list.append(str(key) + ",")
        sql_1 = "".join(sql_1_list)
        if sql_1.endswith(',') == True:
            sql_1 = sql_1.strip(',')
            
        sql_2 = ") VALUE ("
        
        sql_3_list = []
        for key in params.keys():
            sql_3_list.append("%(" + str(key) + ")s,")
        sql_3 = " ".join(sql_3_list)
        if sql_3.endswith(',') == True:
            sql_3 = sql_3.strip(',') + ')'
        
        final_sql = sql_1 + sql_2 + sql_3
        print(final_sql)

        cursor.execute(final_sql, params)
        conn.commit()
        result = 'true'
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return result

@app.route('/api/update_apply', methods=['POST'])
def update_apply():
    conn = None
    cursor = None
    result = 'false'
    final_sql = ''
    try:
        print('update_apply start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 向params追加其他参数
        # params['apply_order_num'] = datetime.now().strftime("%Y%m%d%H%M%S%f") + str(random.randint(10000, 99999))
        if 'apply_order_status' not in params:
            # return make_err_response('缺少openid参数')
            params['apply_order_status'] = 0 # 草稿
        params['apply_order_modify_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if params['apply_order_status'] == 1:
            params['apply_order_submit_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 获取游标
        cursor = conn.cursor()
        # 按数据包的key-value拼接SQL
        sql_1_list = ["UPDATE t_a_application SET "]
        for key in params.keys():
            if key != 'apply_order_num':
                sql_1_list.append(str(key) + ' = ' + "%(" + str(key) + ")s, ")
        sql_1 = "".join(sql_1_list)
        if sql_1.endswith(', ') == True:
            sql_1 = sql_1.strip(', ')

        sql_2 = " WHERE apply_order_num = '%s'" % params['apply_order_num']
        final_sql = sql_1 + sql_2
        
        print(final_sql)

        cursor.execute(final_sql, params)
        conn.commit()
        result = 'true'
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return result

@app.route('/api/get_verification_location', methods=['POST'])
def get_verification_location():
    conn = None
    cursor = None
    appoint_verification_location = ''
    try:
        print('get_verification_location start')
        # 获取数据库链接
        conn = create_conn()
        conn = pymysql.connect(host=config.db_address, user=config.username, passwd=config.password, database=config.database, port=config.port, charset='utf8')
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 获取游标
        cursor = conn.cursor()
        sql = (
            " select toll_station_name",
            " from ",
            " t_t_toll_station ",
            " order by toll_station_id asc "
        )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        rows = cursor.fetchall()
        print(rows)
        if rows:
            appoint_verification_location = rows
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return make_succ_response(appoint_verification_location)

@app.route('/api/get_apply_info_by_apply_order_num', methods=['POST'])
def get_apply_info_by_apply_order_num():
    conn = None
    cursor = None
    apply_info_list = ''
    try:
        print('get_apply_info_by_apply_order_num start')
        # 获取数据库链接
        conn = create_conn()
        # conn = pymysql.connect(host=config.db_address, user=config.username, passwd=config.password, database=config.database, port=config.port, charset='utf8')
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 获取游标
        cursor = conn.cursor()
        sql = (
            " select ",
            " apply_order_id, ",
            " apply_order_num, ",
            " plate_number, ",
            " charge_department, ",
            " vehicle_department, ",
            " driver_mobile_number, ",
            " driver_id_license_cloudID, ",
            " driver_driver_license_cloudID, ",
            " vehicle_license_cloudID, ",
            " over_limit_license_cloudID, ",
            " road_operating_license_cloudID, ",
            " approved_path, ",
            " solution_files_cloudID, ",
            " escort_solution_cloudID, ",
            # " DATE_FORMAT(start_time,'%H:%i') as start_time, ",
            # " DATE_FORMAT(end_time,'%H:%i') as end_time, ",
            # " DATE_FORMAT(start_date,'%Y-%m-%d') as start_date, ",
            # " DATE_FORMAT(end_date,'%Y-%m-%d') as end_date, ",
            " DATE_FORMAT(start_datetime,'%Y-%m-%d %H:%i') as start_datetime, ",
            " DATE_FORMAT(end_datetime,'%Y-%m-%d %H:%i') as end_datetime, ",
            " escort_plate_number_1, ",
            " escort_driver_license_cloudID_1, ",
            " escort_vehicle_license_cloudID_1, ",
            " escort_vehicle_files_cloudID_1, ",
            " gross_weight, ",
            " outer_dimension_length, ",
            " outer_dimension_width, ",
            " outer_dimension_height, ",
            " plate_transport_time, ",
            # " DATE_FORMAT(appoint_verification_time,'%H:%i') as appoint_verification_time, ",
            # " DATE_FORMAT(appoint_verification_date,'%Y-%m-%d') as appoint_verification_date, ",
            " DATE_FORMAT(appoint_verification_datetime,'%Y-%m-%d %H:%i') as appoint_verification_datetime, ",
            " if(toll_station_id is null, 0, toll_station_id) as toll_station_id, ",
            " appoint_verification_location, ",
            " apply_order_status, ",
            " DATE_FORMAT(apply_order_create_time,'%Y-%m-%d %H:%i:%S') as apply_order_create_time, ",
            " DATE_FORMAT(apply_order_modify_time,'%Y-%m-%d %H:%i:%S') as apply_order_modify_time, ",
            " DATE_FORMAT(apply_order_submit_time,'%Y-%m-%d %H:%i:%S') as apply_order_submit_time, ",
            " apply_order_submit_openid, ",
            " adjust_comment "
            " from ",
            " t_a_application ",
            " where apply_order_num = %s " % params['apply_order_num']
        )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        rows = cursor.fetchall()
        print(rows)
        if rows:
            apply_info_list = rows
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return make_succ_response(apply_info_list)

@app.route('/api/get_valid_pic_info_by_apply_order_num', methods=['POST'])
def get_valid_pic_info_by_apply_order_num():
    conn = None
    cursor = None
    valid_pic_info_info_list = ''
    try:
        print('get_valid_pic_info_by_apply_order_num start')
        # 获取数据库链接
        conn = create_conn()
        # conn = pymysql.connect(host=config.db_address, user=config.username, passwd=config.password, database=config.database, port=config.port, charset='utf8')
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 获取游标
        cursor = conn.cursor()
        sql = (
            " select ",
            " apply_order_num, ",
            " valid_vehicle_front_files_cloudID, ",
            " valid_vehicle_back_files_cloudID, ",
            " valid_vehicle_left_front_files_cloudID, ",
            " valid_vehicle_left_back_files_cloudID, ",
            " valid_vehicle_right_front_files_cloudID, ",
            " valid_vehicle_right_back_files_cloudID, ",
            " valid_whole_scene_1_files_cloudID, ",
            " valid_whole_scene_2_files_cloudID ",
            " from ",
            " t_a_application_valid_photo ",
            " where apply_order_num = %s " % params['apply_order_num']
        )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        rows = cursor.fetchall()
        print(rows)
        if rows:
            valid_pic_info_info_list = rows
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return make_succ_response(valid_pic_info_info_list)

@app.route('/api/modify_apply_status', methods=['POST'])
def modify_apply_status():
    conn = None
    cursor = None
    result = 'false'
    try:
        print('modify_apply_status start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        params['verification_datetime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(params)
        # 获取游标
        cursor = conn.cursor()
        sql = (
            "UPDATE t_a_application SET ",
            "apply_order_status = '%s', " % params['apply_order_status'],
            "verification_datetime = '%s', " % params['verification_datetime'],
            "verification_officer_id = '%s', " % params['user_id'],
            "verification_officer_name = '%s', " % params['user_name'],
            "verification_officer_openid = '%s' " % params['user_openid'],
            "WHERE ",
            "apply_order_num = '%s' " % params['apply_order_num']
            )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        conn.commit()
        result = 'true'
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return result

@app.route('/api/modify_apply_status_in_camera_part', methods=['POST'])
def modify_apply_status_in_camera_part():
    conn = None
    cursor = None
    result = 'false'
    try:
        print('modify_apply_status_in_camera_part start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 获取游标
        cursor = conn.cursor()
        sql = (
            "UPDATE t_a_application SET ",
            "apply_order_status = '%s' " % params['apply_order_status'],
            "WHERE ",
            "apply_order_num = '%s' " % params['apply_order_num']
            )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        conn.commit()
        result = 'true'
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return result

@app.route('/api/save_adjust_comment', methods=['POST'])
def save_adjust_comment():
    conn = None
    cursor = None
    result = 'false'
    try:
        print('save_adjust_comment start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        params['verification_datetime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(params)
        # 获取游标
        cursor = conn.cursor()
        sql = (
            "UPDATE t_a_application SET ",
            "apply_order_status = '%s', " % params['apply_order_status'],
            "adjust_comment = '%s', " % params['adjust_comment'],
            "verification_datetime = '%s', " % params['verification_datetime'],
            "verification_officer_id = '%s', " % params['user_id'],
            "verification_officer_name = '%s', " % params['user_name'],
            "verification_officer_openid = '%s' " % params['user_openid'],
            "WHERE ",
            "apply_order_num = '%s' " % params['apply_order_num']
            )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        conn.commit()
        result = 'true'
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return result

@app.route('/api/new_valid_vehicle_photo', methods=['POST'])
def new_valid_vehicle_photo():
    conn = None
    cursor = None
    result = 'false'
    final_sql = ''
    try:
        print('new_valid_vehicle_photo start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 获取游标
        cursor = conn.cursor()
        # 按数据包的key-value拼接SQL
        sql_1_list = ["INSERT INTO t_a_application_valid_photo ("]
        for key in params.keys():
            sql_1_list.append(str(key) + ",")
        sql_1 = "".join(sql_1_list)
        if sql_1.endswith(',') == True:
            sql_1 = sql_1.strip(',')
            
        sql_2 = ") VALUE ("
        
        sql_3_list = []
        for key in params.keys():
            sql_3_list.append("%(" + str(key) + ")s,")
        sql_3 = " ".join(sql_3_list)
        if sql_3.endswith(',') == True:
            sql_3 = sql_3.strip(',') + ')'
        
        final_sql = sql_1 + sql_2 + sql_3
        print(final_sql)

        cursor.execute(final_sql, params)
        conn.commit()
        result = 'true'
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return result

@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')

@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)

@app.route('/api/recive_callback', methods=['POST'])
def recive_callback():
    err_msg = ''
    params = ''
    recive_callback_data = {
        'uid': None,
        'serviceId': None,
        'requestId': None,
        'callId': None,
        'caller': None,
        'callee': None,
        'inviteTime': None,
        'ringTime': None,
        'answerTime': None,
        'disconnectTime': None,
        'userKey': None,
        'serviceDuration': None,
        'serviceResult': None,
        'endReason': None,
        'sipCode': None
    }
    try:
        # 获取请求体参数
        params = request.get_json()
        # 规整数据
        for key in recive_callback_data.keys():
            if key in params.keys():
                recive_callback_data[key] = params[key]
        # 拼接数据写入DB
        recive_callback_data['applyOrderNum'] = params['requestId'] if 'requestId' in params.keys() else None
        recive_callback_data['feedbackLogData'] = json.dumps(recive_callback_data)
        # 获取数据库链接
        conn = create_conn()
        # 获取游标
        cursor = conn.cursor()

        sql = [
            " INSERT INTO t_a_call_feedback ( ",
            " feedbackLogData ",
            ",applyOrderNum ",
            ",uid ",
            ",serviceId ",
            ",requestId ",
            ",callId ",
            ",caller ",
            ",callee ",
            ",inviteTime ",
            ",ringTime ",
            ",answerTime ",
            ",disconnectTime ",
            ",userKey ",
            ",serviceDuration ",
            ",serviceResult ",
            ",endReason ",
            ",sipCode ",
            ") VALUES ( ",
            " %(feedbackLogData)s ",
            ",%(applyOrderNum)s ",
            ",%(uid)s ",
            ",%(serviceId)s ",
            ",%(requestId)s ",
            ",%(callId)s ",
            ",%(caller)s ",
            ",%(callee)s ",
            ",%(inviteTime)s ",
            ",%(ringTime)s ",
            ",%(answerTime)s ",
            ",%(disconnectTime)s ",
            ",%(userKey)s ",
            ",%(serviceDuration)s ",
            ",%(serviceResult)s ",
            ",%(endReason)s ",
            ",%(sipCode)s ",
            ") ",
        ]
        print(" ".join(sql))
        cursor.execute(" ".join(sql), recive_callback_data)
        conn.commit()
        # 基于返回的数据，做逻辑判断，是否重新发起外呼
        check_callback_data_and_call(recive_callback_data)
    except Exception as e:
        err_msg = str(e)
        return make_err_response(err_msg)
    finally:
        print('------- recive_callback_data -------')
        print(recive_callback_data)
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return make_succ_empty_response()

def check_callback_data_and_call(recive_callback_data):
    conn = None
    cursor = None
    try:
        print('------ check_callback_data_and_call --------')
        # 获取数据库链接
        conn = create_conn()
        # 获取游标
        cursor = conn.cursor()

        # 检查返回数据中，外呼的实际结果是否已成功，如果成功了，则不再重复呼叫
        # 被叫已接听
        if recive_callback_data['endReason'] == '0' and recive_callback_data['sipCode'] == '0':
            pass
        # 被叫拒接或忙/被叫未接（有振铃）
        if (recive_callback_data['endReason'] == '100000006' and recive_callback_data['sipCode'] == '500') or (recive_callback_data['endReason'] == '100000007' and recive_callback_data['sipCode'] == '603'):
            # 外呼的实际结果并未成功，检查此报备单外呼总次数
            sql = "SELECT COUNT(1) AS total_call_times FROM t_a_call_feedback WHERE applyOrderNum = '%s' " % recive_callback_data['applyOrderNum']
            cursor.execute(sql)
            row = cursor.fetchone()
            if int(row['total_call_times']) < 3:
                print('------ 报备单%s自动外呼第%s次 --------' % (recive_callback_data['applyOrderNum'], int(row['total_call_times']) + 1))
                # 若此报备单外呼总次数未超过3，则继续外呼（等待30秒）
                time.sleep(30)
                # 获取外呼请求参数（最新）
                sql_params = "SELECT * FROM t_a_call_log WHERE applyOrderNum = %s ORDER BY callLogId DESC" % recive_callback_data['applyOrderNum']
                cursor.execute(sql_params)
                call_params = cursor.fetchone()
                # 发起外呼
                url = 'http://123.56.67.182:19201/vms'
                headers = {
                    'Content-Type': 'application/json;charset=utf-8',
                }
                timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
                password_str = '300fd5c0-bbcf-4520-8b9f-6c5e1521acd2' + timestamp_str
                data = {
                    'uid': call_params['uid'],
                    'serviceType': 2,
                    'timestamp': timestamp_str,
                    'password': hashlib.md5(password_str.encode('utf-8')).hexdigest(),
                    'callee': call_params['callee'],
                    'playWay': 1,
                    'playTimes': 2,
                    'templateId': call_params['templateId'],
                    'requestId': call_params['requestId'],
                    'content': call_params['content']
                }
                print('------check_callback_data_and_call  data ------')
                print(data)
                result = requests.post(url, headers=headers, data=json.dumps(data))
                print(result.content.decode('utf-8'))

                # 将请求数据和返回数据写入DB
                add_call_log(data,result)
            else:
                # 若此报备单外呼总次数已达3次，则停止外呼
                pass
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/call', methods=['POST'])
def call():
    try:
        # 获取请求体参数
        params = request.get_json()
        print('call start')

        content = '你好，车牌号为%s的超限运输车辆在%s收费站申请验证，请及时处理！' % (params['plate_number'], params['toll_station'])
        url = 'http://123.56.67.182:19201/vms'
        headers = {
            'Content-Type': 'application/json;charset=utf-8',
        }
        timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = '300fd5c0-bbcf-4520-8b9f-6c5e1521acd2' + timestamp_str
        data = {
            'uid': '75e07e8c-89db-4492-b946-9d8a30570e37',
            'serviceType': 2,
            'timestamp': timestamp_str,
            'password': hashlib.md5(password_str.encode('utf-8')).hexdigest(),
            'callee': params['callee'],
            'playWay': 1,
            'playTimes': 2,
            'templateId': 'ef32276a-9495-4079-8887-9665754632cb',
            'requestId': params['requestId'],
            'content': content
        }
        print('------ data ------')
        print(data)
        result = requests.post(url, headers=headers, data=json.dumps(data))
        print(result.content.decode('utf-8'))

        # 将请求数据和返回数据写入DB
        add_call_log(data,result)
    except Exception as e:
        return make_err_response(str(e))
    finally:
        return make_succ_response(result.content.decode('utf-8'))

def add_call_log(data, result):
    conn = None
    cursor = None
    try:
        # 获取数据库链接
        conn = create_conn()
        # 获取游标
        cursor = conn.cursor()

        sql = [
            " INSERT INTO t_a_call_log ( ",
            " callData ",
            ",callResponseData ",
            ",applyOrderNum ",
            ",uid ",
            ",serviceType ",
            ",callTimestamp ",
            ",callPassword ",
            ",caller ",
            ",callee ",
            ",playWay ",
            ",playTimes ",
            ",ringId ",
            ",templateId ",
            ",requestId ",
            ",content ",
            ",keyTimeout ",
            ",keyList ",
            ",respCode ",
            ",serviceId ",
            ") VALUES ( ",
            " %(callData)s ",
            ",%(callResponseData)s ",
            ",%(applyOrderNum)s ",
            ",%(uid)s ",
            ",%(serviceType)s ",
            ",%(callTimestamp)s ",
            ",%(callPassword)s ",
            ",%(caller)s ",
            ",%(callee)s ",
            ",%(playWay)s ",
            ",%(playTimes)s ",
            ",%(ringId)s ",
            ",%(templateId)s ",
            ",%(requestId)s ",
            ",%(content)s ",
            ",%(keyTimeout)s ",
            ",%(keyList)s ",
            ",%(respCode)s ",
            ",%(serviceId)s ",
            ") ",
        ]
        args = {
             'callData': json.dumps(data)
            ,'callResponseData': result.content.decode('utf-8')
            ,'applyOrderNum': data['requestId']
            ,'uid': data['uid']
            ,'serviceType': data['serviceType']
            ,'callTimestamp': data['timestamp']
            ,'callPassword': data['password']
            ,'caller': data['password']
            ,'callee': data['callee']
            ,'playWay': data['playWay']
            ,'playTimes': data['playTimes']
            ,'ringId': data['ringId'] if 'ringId' in data.keys() else None
            ,'templateId': data['templateId'] if 'templateId' in data.keys() else None
            ,'requestId': data['requestId']
            ,'content': data['content'].encode('utf-8')
            ,'keyTimeout': data['keyTimeout'] if 'keyTimeout' in data.keys() else None
            ,'keyList': data['keyList'] if 'keyList' in data.keys() else None
            ,'respCode': json.loads(result.content.decode('utf-8'))['respCode']
            ,'serviceId': json.loads(result.content.decode('utf-8'))['serviceId']
        }
        print(" ".join(sql))
        cursor.execute(" ".join(sql), args)
        conn.commit()
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/valid_officer', methods=['POST'])
def valid_officer():
    conn = None
    cursor = None
    officer_info = []
    try:
        print('valid_officer start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 获取游标
        cursor = conn.cursor()
        # 检查账号密码
        sql = "select * from t_u_user where user_mobile = '%s' and user_password = '%s'" % (params['user_mobile'], params['user_password'])
        print(sql)
        cursor.execute(sql)
        row = cursor.fetchone()
        # 账号密码验证通过，绑定用户
        if row:
            officer_info = row
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return make_succ_response(officer_info)
    
@app.route('/api/unbind_officer', methods=['POST'])
def unbind_officer():
    conn = None
    cursor = None
    result = 'false'
    try:
        print('unbind_officer start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 获取游标
        cursor = conn.cursor()
        sql = (
            "UPDATE t_u_user SET ",
            "user_openid = null ",
            "WHERE ",
            "user_id = '%s' " % params['user_id']
            )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        conn.commit()
        result = 'true'
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return result

@app.route('/api/get_apply_info_with_call_number', methods=['POST'])
def get_apply_info_with_call_number():
    conn = None
    cursor = None
    get_apply_info_with_call_number = ''
    try:
        print('get_apply_info_with_call_number start')
        # 获取数据库链接
        conn = create_conn()
        # conn = pymysql.connect(host=config.db_address, user=config.username, passwd=config.password, database=config.database, port=config.port, charset='utf8')
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 获取游标
        cursor = conn.cursor()
        sql = (
            " select ",
            " office.duty_phone ",
            ",application.apply_order_num ",
            ",application.plate_number ",
            ",application.appoint_verification_location ",
            " from ",
            " t_a_application application, ",
            " t_t_toll_station toll_station, ",
            " t_u_office_account office ",
            " where application.apply_order_num = %s " % params['apply_order_num'],
            " and application.toll_station_id = toll_station.toll_station_id ",
            " and toll_station.office_id = office.office_id "
        )
        print(" ".join(sql))
        cursor.execute(" ".join(sql))
        row = cursor.fetchone()
        print(row)
        if row:
            get_apply_info_with_call_number = row
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return make_succ_response(get_apply_info_with_call_number)

@app.route('/api/get_apply_order_call_records', methods=['POST'])
def get_apply_order_call_records():
    conn = None
    cursor = None
    get_apply_order_call_records = ''
    try:
        print('get_apply_order_call_records start')
        # 获取数据库链接
        conn = create_conn()
        # conn = pymysql.connect(host=config.db_address, user=config.username, passwd=config.password, database=config.database, port=config.port, charset='utf8')
        # 获取请求体参数
        params = request.get_json()
        print(params)
        # 获取游标
        cursor = conn.cursor()
        sql = (
            " SELECT  ",
            " success_records.* ",
            ",total_records.* FROM ",
            "(SELECT  ",
            " count( 1 ) AS success_records_times ",
            ",max( inviteTime ) AS success_record_latest_datetime ",
            " FROM ",
            " t_a_call_feedback ",
            " WHERE ",
            " applyOrderNum = %(applyOrderNum)s AND ",
            " serviceResult = %(serviceResult)s ",
            ") success_records, ",
            "(SELECT  ",
            " count( 1 ) AS total_records_times ",
            ",max( inviteTime ) AS total_record_latest_datetime ",
            " FROM ",
            " t_a_call_feedback ",
            " WHERE ",
            " applyOrderNum = %(applyOrderNum)s ",
            ") total_records "
        )
        args = {
            'applyOrderNum': params['apply_order_num'],
            'serviceResult': '0'
        }
        print(" ".join(sql))
        cursor.execute(" ".join(sql), args)
        row = cursor.fetchone()
        print(row)
        if row:
            get_apply_order_call_records = row
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return make_succ_response(get_apply_order_call_records)


if __name__ == '__main__':
    pass
    # print('test')
    # call()
    # print(round(time.time() * 1000))
    # current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    # print(current_time)
    # conn = pymysql.connect(
    #     host='sh-cynosdbmysql-grp-hsc16e2c.sql.tencentcdb.com',
    #     user='root',
    #     passwd='kqSJ9b7J',
    #     database='remote_validation',
    #     port=22114,
    #     charset='utf8',
    #     cursorclass=pymysql.cursors.DictCursor)
    # cursor = conn.cursor()
    # apply_order_num = '1684683667557'
    # sql = "SELECT COUNT(1) AS total_call_times FROM t_a_call_feedback WHERE applyOrderNum = '%s' " % apply_order_num
    # cursor.execute(sql)
    # row = cursor.fetchone()
    # print(row['total_call_times'])
