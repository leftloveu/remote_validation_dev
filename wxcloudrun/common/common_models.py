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

import pymysql
import config
import math

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
