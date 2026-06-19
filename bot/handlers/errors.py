import logging

from aiogram import Router
from aiogram.types import ErrorEvent

from bot.keyboards import main_kb
from bot.wb_client import WbAuthError, WbRateLimitError
from bot.utils import get_account_name

router = Router()
logger = logging.getLogger(__name__)


@router.errors()
async def error_handler(event: ErrorEvent) -> None:
    logger.exception("Unhandled update: %s", event.update)

    tg_id = None
    if event.update.callback_query:
        tg_id = event.update.callback_query.from_user.id
    elif event.update.message:
        tg_id = event.update.message.from_user.id

    acc_name = await get_account_name(tg_id) if tg_id else None
    kb = main_kb(acc_name)

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
