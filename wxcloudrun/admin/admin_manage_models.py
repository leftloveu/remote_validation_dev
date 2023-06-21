#!/usr/bin/python
# -*- coding: utf-8 -*-
#############################
# Function: 后台数据处理
# Author: 周若凡
# E-mail: zrfedward@gmail.com
# Date: 2017-06
# Modified by:
#   1.
#############################

import os, sys
import pymysql
import config

_dir = os.path.dirname(os.path.abspath(__file__))
_updir = os.path.abspath(os.path.join(_dir, '..'))
if _updir not in sys.path:
    sys.path.insert(0, _updir)

from flask import session, g

# 初始化DB链接
def create_conn():
    conn = None
    try:
        conn = pymysql.connect(host=config.db_address, user=config.username, passwd=config.password, database=config.database, port=config.port, charset='utf8', cursorclass=pymysql.cursors.DictCursor)
    except Exception as e:
        print(str(e))
    return conn


def login_check(user_mobile, user_password):
    '''
    @function: 用于验证用户
    @args:
        @user_name: 用户名
        @user_password: 密码
    @return result(True or False)
    '''
    result = False
    conn, cursor = None, None
    try:
        conn = create_conn()
        cursor = conn.cursor()
        sql = [
            " SELECT ",
            " user_id ",
            ",user_name ",
            ",user_mobile ",
            ",user_role ",
            ",CASE user_role  ",
            " WHEN 'officer' then '执法人员' ",
            " WHEN 'driver' then '司机' ",
            " END AS user_role_name ",
            ",user_associated_account ",
            " FROM t_u_user where  ",
            " user_mobile = '%s' " % user_mobile,
            " AND user_password = '%s' " % user_password,

        ]
        cursor.execute("".join(sql))
        row = cursor.fetchone()
        print(row)
        # 验证通过，将user_name加入session
        if row and len(row) > 0:
            result = True
            session['user_info'] = row
        print(session)
    except Exception as e:
        print(str(e))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return result
