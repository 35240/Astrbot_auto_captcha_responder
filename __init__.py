# 安全导出 AutoCaptchaResponder，避免顶层导入时阻塞宿主
try:
    from .main import AutoCaptchaResponder
except Exception:
    class AutoCaptchaResponder:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("AutoCaptchaResponder 无法导入真实实现，检查日志。")
