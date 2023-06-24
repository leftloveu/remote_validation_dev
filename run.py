# 创建应用实例
import sys

from wxcloudrun import app
from flask import redirect

# 定义blueprints
blueprints = (
    ('wxcloudrun.admin.admin_manage_views.admin_manage_bp', '/admin_manage'),
    ('wxcloudrun.application.application_manage_views.application_manage_bp', '/application_manage'),
    )

# 注册blueprints
for mod_path, mount_point in blueprints:
    parts = mod_path.split('.')
    _path = '.'.join(parts[:-1])
    bp_name = parts[-1]
    # mod = __import__(_path, None, None, [bp_name], -1)
    mod = __import__(_path, None, None, [bp_name], 0)
    bp = getattr(mod, bp_name)
    app.register_blueprint(bp, url_prefix=mount_point)

# 启动Flask Web服务
if __name__ == '__main__':
    app.run(host=sys.argv[1], port=sys.argv[2])
    # app.run(host='0.0.0.0', port=80)