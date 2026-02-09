import re
import asyncio

try:
    from astrbot.api.event import filter, AstrMessageEvent
    from astrbot.api.star import Context, Star, register
    from astrbot.core import AstrBotConfig
except Exception:
    class Context:
        def __init__(self):
            self._config = {}

        def get_plugin_config(self):
            return self._config
    class Star:
        def __init__(self, context: Context, *_args, **_kwargs):
            self.context = context

    class DummyFilter:
        class EventMessageType:
            GROUP_MESSAGE = 0

        def event_message_type(self, *_args, **_kwargs):
            def deco(func):
                return func
            return deco

    def register(*_args, **_kwargs):
        def deco(cls):
            return cls
        return deco

    filter = DummyFilter()

    class AstrMessageEvent:  # type: ignore[override]
        message_str: str = ""
        self_id: str = ""
        message_id: str = ""
        is_at_or_wake_command: bool = False

        class _MsgObj:
            message_id: str = ""

        message_obj = _MsgObj()

        def get_sender_id(self) -> str:
            return ""

        async def send(self, *_args, **_kwargs):
            return

        def plain_result(self, text: str):
            return text


@register("auto_captcha_responder", "AutoCaptcha", "自动识别并回复进群验证码", "1.0.0")
class AutoCaptchaResponder(Star):
    def __init__(self, context: Context, config: "AstrBotConfig | dict | None" = None):  # type: ignore[name-defined]
        super().__init__(context)
        cfg = config or {}
        self.enabled = bool(cfg.get("enabled", True))
        self.require_at_bot = bool(cfg.get("require_at_bot", True))
        self.quote_message = bool(cfg.get("quote_message", True))
        try:
            self.delay_seconds = float(cfg.get("delay_seconds", 0) or 0)
        except Exception:
            self.delay_seconds = 0.0
        if self.delay_seconds < 0:
            self.delay_seconds = 0.0
        base_patterns = [
            r'请回复[：:\s]*["“]?([0-9A-Za-z]{3,8})["”]?\s*验证(?:身份|)',
            r'输入[：:\s]*[「\"“]?(.+?)[」\"”]?\s*加入(?:群聊|群)',
            r'请输入验证码[：:\s]*["“]?(.+?)["”]?',
            r'回复\s*["“]?(\d{4,6})["”]?\s*通过验证',
            r'验证码[：:\s]*["“]?([0-9A-Za-z]{4,10})["”]?',
            r'验证码[：:\s]*["“]?(\d{4,6})["”]?',
            r'请发送\s*(\d{4,6})\s*完成验证',
            r'请回复[：:\s]*["“]?(.+?)["”]?\s*验',
            r'输入[：:\s]*["“]?(.+?)["”]?\s*以验证',
        ]
        custom_patterns = cfg.get("custom_patterns") or []
        self.patterns = base_patterns + [p for p in custom_patterns if isinstance(p, str) and p.strip()]

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def listen_group_captcha(self, event: AstrMessageEvent):
        if not getattr(self, "enabled", True):
            return

        if getattr(self, "require_at_bot", True):
            if not getattr(event, "is_at_or_wake_command", False):
                return

        text = (getattr(event, "message_str", "") or "").strip()
        if not text:
            return

        for pattern in self.patterns:
            m = re.search(pattern, text)
            if not m:
                continue
            code = m.group(1).strip()
            if not code:
                continue

            if getattr(self, "delay_seconds", 0) > 0:
                await asyncio.sleep(self.delay_seconds)

            # 按你的要求：回复时只发送验证码本体，不带任何前缀
            yield event.plain_result(code)
            return
