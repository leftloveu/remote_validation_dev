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

# 初始化日志
# logger = logging.getLogger('log')
logger = logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
    filename="test.log"
    )

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
    logger.debug('/api/check_user_status')
    conn = None
    cursor = None
    user_info = ''
    try:
        logger.debug('check_user_status start')
        # 获取数据库链接
        conn = create_conn()
        # 获取请求体参数
        params = request.get_json()
        logger.debug(params)
        # 检查openid参数
        if 'openid' not in params:
            return make_err_response('缺少openid参数')
        # openid存在，开始校验此openid是否绑定角色
        # 获取游标
        cursor = conn.cursor()
        sql = (
            " select user_id",
            ",user_name ",
            ",user_id_card_num ",
            ",user_mobile ",
            ",user_openid ",
            ",user_role ",
            ",user_associated_account ",
            " from ",
            " t_u_user ",
            " where ",
            " user_openid = '%s'" % params['openid']
        )
        logger.debug(" ".join(sql))
        cursor.execute(" ".join(sql))
        row = cursor.fetchone()
        logger.debug(row)
        if row:
            user_info = row
    except Exception as e:
        logger.error(str(e))
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
    office_id = ''
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
        # 检查账号密码
        sql = "select office_id from t_u_office_account where office_account = '%s' and office_password = '%s'" % (params['user_name'], params['password'])
        print(sql)
        cursor.execute(sql)
        row = cursor.fetchone()
        # 账号密码验证通过，绑定用户
        if row:
            sql = (
                "INSERT INTO t_u_user (",
                    "user_openid, ",
                    "user_role, ",
                    "user_associated_account ",
                ") VALUE ( ",
                    "%(user_openid)s, ",
                    "%(user_role)s, ",
                    "%(user_associated_account)s) "
            )
            args = {
                'user_openid': params['openid'],
                'user_role': params['role'],
                'user_associated_account': params['user_name']
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
            ",DATE_FORMAT(apply_order_submit_time,'%Y-%m-%d %H:%i:%S') as apply_order_submit_time ",
            ",plate_number ",
            ",approved_path ",
            ",appoint_verification_location ",
            ",apply_order_status ",
            " from ",
            " t_a_application ",
            " where ",
            " apply_order_submit_openid = '%s'" % params['openid'],
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
            "AND d.apply_order_status in (1, 2)",
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
            " AND apply_order_status = 3 ",
            " AND now() <= end_time",
            " order by end_time asc "
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
            " escort_solution_cloudID, ",
            " DATE_FORMAT(start_time,'%Y-%m-%d %H:%i:%S') as start_time, ",
            " DATE_FORMAT(end_time,'%Y-%m-%d %H:%i:%S') as end_time, ",
            " gross_weight, ",
            " outer_dimension_length, ",
            " outer_dimension_width, ",
            " outer_dimension_height, ",
            " plate_transport_time, ",
            " DATE_FORMAT(appoint_verification_time,'%Y-%m-%d %H:%i:%S') as appoint_verification_time, ",
            " toll_station_id, ",
            " appoint_verification_location, ",
            " apply_order_status, ",
            " DATE_FORMAT(apply_order_create_time,'%Y-%m-%d %H:%i:%S') as apply_order_create_time, ",
            " DATE_FORMAT(apply_order_modify_time,'%Y-%m-%d %H:%i:%S') as apply_order_modify_time, ",
            " DATE_FORMAT(apply_order_submit_time,'%Y-%m-%d %H:%i:%S') as apply_order_submit_time, ",
            " apply_order_submit_openid ",
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
        print(params)
        # 获取游标
        cursor = conn.cursor()
        sql = (
            "UPDATE t_a_application SET ",
            "apply_order_status = '%s', " % params['apply_order_status'],
            "adjust_comment = '%s' " % params['adjust_comment'],
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
