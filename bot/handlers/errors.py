import logging

from aiogram import Router
from aiogram.types import ErrorEvent

from bot.keyboards import main_kb
from bot.wb_client import WbAuthError, WbRateLimitError

router = Router()
logger = logging.getLogger(__name__)


@router.errors()
async def error_handler(event: ErrorEvent) -> None:
    logger.exception("Unhandled update: %s", event.update)
    kb = main_kb()

    error_text = "❌ Произошла непредвиденная ошибка. Попробуй ещё раз."
    if isinstance(event.update, Exception):
        exc = event.update
    elif hasattr(event, 'update') and hasattr(event.update, 'message') and event.update.message:
        exc = event.exception if hasattr(event, 'exception') else None
    else:
        exc = None

    if isinstance(exc, WbAuthError):
        error_text = f"❌ {exc}"
    elif isinstance(exc, WbRateLimitError):
        error_text = f"⏰ {exc}"

    if event.update.callback_query:
        callback = event.update.callback_query
        try:
            await callback.message.edit_text(error_text)
        except Exception:
            pass
        try:
            await callback.bot.send_message(
                callback.from_user.id,
                "Используй кнопки внизу экрана для навигации.",
                reply_markup=kb,
            )
        except Exception:
            pass
    elif event.update.message:
        message = event.update.message
        try:
            await message.answer(error_text, reply_markup=kb)
        except Exception:
            pass
