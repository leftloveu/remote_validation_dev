from flask import Blueprint, render_template, session, url_for, redirect, request

import functools, json
from wxcloudrun.admin import admin_manage_models
from wxcloudrun.common import common_models

# 注册blueprint
admin_manage_bp = Blueprint('admin_manage_bp', __name__, template_folder='templates', static_folder='static')


# 装饰器：检查当前用户是否登录有效
def is_login(func):
    @functools.wraps(func)
    def check_session(*args, **kwargs):
        # Do something
        if session.get('user_info'):
            pass
        else:
            return redirect(url_for('.login'))
        return func(*args, **kwargs)
    return check_session


# 登录页面
@admin_manage_bp.route('/login', methods=['GET', 'POST'])
def login():
    err_msg = request.args.get('err_msg', None)
    return render_template("/admin/login_manage.html", err_msg=err_msg)


# 后台管理系统index页面
@admin_manage_bp.route('/home', methods=['POST','GET'])
@is_login
def home():
    session['current_page'] = 'home'
    return render_template("/admin/home.html")


# 登录验证
@admin_manage_bp.route('/login_valid', methods=['POST', 'GET'])
def login_valid():
    params = request.form.to_dict()
    user_mobile = params['user_mobile']
    user_password = params['user_password']
    if request.method == 'POST':
        if admin_manage_models.login_check(user_mobile, user_password):
            return redirect(url_for('.home'))
        else:
            return redirect(url_for('.login', err_msg="false"))


# 系统登出
@admin_manage_bp.route('logout', methods=['POST', 'GET'])
def logout():
    # 清除session信息
    session.clear()
    return redirect(url_for('.login'))


# 个人中心
@admin_manage_bp.route('/my_center', methods=['POST','GET'])
@is_login
def my_center():
    session['current_page'] = 'my_center'
    return render_template("/admin/my_center.html")


# 个人中心
@admin_manage_bp.route('/application_manage', methods=['POST','GET'])
@is_login
def application_manage():
    # 获取page的值，默认为1
    page = request.args.get('page', 1)

    if session['user_info']['user_associated_account'] == 'YZDZHZX':
        # 支队账号可查全部数据
        extra_where_sql = " 1=1 order by verification_datetime desc, apply_order_submit_time desc"
    else:
        # 大队账号仅可查大队数据
        extra_where_sql_list = [
            " 1=1 and toll_station_id in ( ",
            " select ",
            " station.toll_station_id ",
            " from ",
            " t_t_toll_station station",
            ",t_u_office_account account",
            " WHERE station.office_id = account.office_id ",
            " and account.office_account = '%s')" % session['user_info']['user_associated_account'],
            " order by verification_datetime desc, apply_order_submit_time desc "
        ]
        extra_where_sql = " ".join(extra_where_sql_list)

    # 从URL获取到参数（request.args），复制到dict_item
    dict_item = {}
    for key in request.args:
        dict_item[key] = request.args[key]

    if 'page' in dict_item:
        del dict_item['page']
    if 'err_msg' in dict_item:
        del dict_item['err_msg']
    if 'apply_order_status' in dict_item and int(dict_item['apply_order_status']) == -1:
        del dict_item['apply_order_status']

    application_list, application_total_page, per_page, row_count = common_models.search(
                                                                    "t_a_application",
                                                                    dict_item,
                                                                    {
                                                                        'page': page,
                                                                        'extra_where_sql': extra_where_sql
                                                                    }
    )

    session['current_page'] = 'application_manage'
    return render_template("/application/application_manage.html",
                           application_list=application_list,
                           total_page=application_total_page,
                           page=page,
                           row_count=row_count,
                           dict_item=dict_item
                           )