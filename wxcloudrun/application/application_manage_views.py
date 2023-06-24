from flask import Blueprint, render_template, session, url_for, redirect, request

import functools, json, requests, datetime
from wxcloudrun.admin.admin_manage_views import is_login
from wxcloudrun.application import application_manage_models

# 注册blueprint
application_manage_bp = Blueprint('application_manage_bp', __name__, template_folder='templates', static_folder='static')


# 查看申报单照片详情
@application_manage_bp.route('/show_detail', methods=['POST','GET'])
@is_login
def show_detail():
    wx_download_file_list = []
    wx_download_file_url_list = []
    apply_order_num = request.args.get('apply_order_num', '')
    show_detail_current_page = request.args.get('show_detail_current_page', 'home')

    session['show_detail_current_page'] = show_detail_current_page
    # 从session中尝试获取文件
    session_name = 'wx_download_file_%s' % apply_order_num

    if session.get(session_name) and session[session_name]['wx_download_file_list_expire_time'].replace(tzinfo=None) > datetime.datetime.now():
        wx_download_file_list = session[session_name]['wx_download_file_list']
    else:
        # 基于apply_order_num获取申报单中的照片/文件以及现场验证照片
        wx_download_file_object = application_manage_models.get_files_list_by_apply_order_num(apply_order_num)
        if 'errcode' in wx_download_file_object.keys() and wx_download_file_object['errcode'] == 0:
            # 获取成功，将数据存储到session中，并设置过期时间2个小时），减少接口调用
            wx_download_file_list_expire_time = datetime.datetime.now() + datetime.timedelta(hours=2)
            wx_download_file_list_session_object = {
                'wx_download_file_list': wx_download_file_object['file_list'],
                'wx_download_file_list_expire_time': wx_download_file_list_expire_time
            }
            session[session_name] = wx_download_file_list_session_object
            wx_download_file_list = wx_download_file_object['file_list']

    for item in wx_download_file_list:
        if 'download_url' in item.keys():
            wx_download_file_url_list.append(item['download_url'])
    wx_download_file_url_list.sort()

    return render_template("/application/show_detail.html",
                           apply_order_num=apply_order_num,
                           wx_download_file_url_list=wx_download_file_url_list
                           )