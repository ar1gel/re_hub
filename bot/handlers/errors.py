import logging

from aiogram import Router
from aiogram.types import ErrorEvent

from bot.keyboards import back_button

router = Router()
logger = logging.getLogger(__name__)


@router.errors()
async def error_handler(event: ErrorEvent) -> None:
    logger.exception("Unhandled update: %s", event.update)

    if event.update.callback_query:
        callback = event.update.callback_query
        try:
            await callback.message.edit_text(
                "❌ Произошла непредвиденная ошибка. Попробуй ещё раз.",
                reply_markup=back_button(),
            )
            await callback.answer()
        except Exception:
            pass
    elif event.update.message:
        message = event.update.message
        try:
            await message.answer(
                "❌ Произошла непредвиденная ошибка. Попробуй ещё раз.",
                reply_markup=back_button(),
            )
        except Exception:
            pass
