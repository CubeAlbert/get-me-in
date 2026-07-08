"""进程生命周期管理 — 统一的退出清理入口。

各模块通过 ``register_shutdown()`` 注册清理 hook，
``shutdown()`` 在进程退出前按注册逆序执行。

用法:
    # 模块内注册
    from src.lifecycle import register_shutdown
    register_shutdown(hook=_cleanup, name="memory")

    # main.py 退出前
    from src.lifecycle import shutdown
    shutdown()
"""

from src.logger import get_logger

logger = get_logger(__name__)

_shutdown_hooks: list[tuple[str, callable]] = []


def register_shutdown(hook, *, name: str = "") -> None:
    """注册一个退出清理 hook。

    同一 name 可重复注册，每次调用都追加。

    Args:
        hook: 无参可调用对象，异常由调用方捕获并记日志。
        name: hook 的可读名称，用于日志。
    """
    _shutdown_hooks.append((name, hook))
    logger.debug("lifecycle: 注册 shutdown hook [%s]", name or "unnamed")


def shutdown() -> None:
    """执行所有已注册的清理 hook，逆序调用。

    每个 hook 的异常会被捕获并记日志，不影响后续 hook 执行。
    """
    hooks = list(_shutdown_hooks)  # snapshot，避免执行中修改
    if not hooks:
        return

    logger.info("lifecycle: 执行 %d 个 shutdown hook...", len(hooks))
    for name, hook in reversed(hooks):
        try:
            logger.debug("lifecycle: shutdown [%s]", name or "unnamed")
            hook()
        except Exception:
            logger.exception("lifecycle: shutdown hook [%s] 异常", name or "unnamed")
    logger.info("lifecycle: shutdown 完成")
