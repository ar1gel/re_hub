import logging

from aiogram import Router
from aiogram.types import ErrorEvent

from bot.keyboards import main_kb

router = Router()
logger = logging.getLogger(__name__)


@router.errors()
async def error_handler(event: ErrorEvent) -> None:
    logger.exception("Unhandled update: %s", event.update)
    kb = main_kb()

    if event.update.callback_query:
        callback = event.update.callback_query
        try:
            await callback.message.edit_text(
                "❌ Произошла непредвиденная ошибка. Попробуй ещё раз.",
            )
        except Exception:
            pass
        try:
            await callback.bot.send_message(
                callback.from_user.id,
                "Произошла ошибка. Используй кнопки внизу экрана для навигации.",
                reply_markup=kb,
            )
        except Exception:
            pass
    elif event.update.message:
        message = event.update.message
        try:
            await message.answer(
                "❌ Произошла непредвиденная ошибка. Попробуй ещё раз.",
                reply_markup=kb,
            )
        except Exception:
            pass
