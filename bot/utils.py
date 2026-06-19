from __future__ import annotations

from html import escape
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import Message

from db.repository import get_ignore_list, get_accounts, get_account_by_id
from db.models import WbAccount


def esc(val, default: str = "—") -> str:
    if val is None:
        return default
    return escape(str(val))


def filter_by_ignore_list(
    items: list[dict],
    account: WbAccount,
    code_keys: str | list[str] = "vendorCode",
) -> list[dict]:
    patterns = get_ignore_list(account)
    if not patterns:
        return items

    if isinstance(code_keys, str):
        code_keys = [code_keys]

    def _is_ignored(item: dict) -> bool:
        for k in code_keys:
            val = item.get(k)
            if not val:
                continue
            val_str = str(val).lower()
            for p in patterns:
                if val_str == p.lower() or p.lower() in val_str:
                    return True
        return False

    return [i for i in items if not _is_ignored(i)]


async def get_selected_account(tg_id: int) -> WbAccount | None:
    from bot.menu import get_account as get_selected_id
    from db.engine import get_session

    selected_id = get_selected_id(tg_id)
    async with get_session() as session:
        accounts = await get_accounts(session, tg_id)
        if not accounts:
            return None
        if selected_id:
            for acc in accounts:
                if acc.id == selected_id:
                    return acc
        return accounts[0]


async def get_account_name(tg_id: int) -> str | None:
    acc = await get_selected_account(tg_id)
    return acc.name if acc else None


async def ensure_account(message: Message) -> WbAccount | None:
    """Check for selected account; send error if missing, return None."""
    account = await get_selected_account(message.from_user.id)
    if not account:
        from bot.keyboards import main_kb
        from bot.menu import set_menu
        acc_name = await get_account_name(message.from_user.id)
        await message.answer(
            "❌ Сначала добавь аккаунт WB.\n\nНажми «Аккаунты» в главном меню.",
            reply_markup=main_kb(acc_name),
        )
        set_menu(message.from_user.id, "main")
    return account


async def call_wb(account: WbAccount, method: str, **kwargs):
    """Call a WB API method with standard error handling. Returns result or None."""
    from bot.wb_client import WbClient
    async with WbClient(account.token) as client:
        func = getattr(client, method)
        return await func(**kwargs)


MESSAGE_LIMIT = 32000


def chunk_message(header: str, rows: list[str], limit: int = MESSAGE_LIMIT) -> list[str]:
    """Split header + rows into message-sized chunks."""
    parts: list[str] = []
    chunk = header
    for r in rows:
        if len(chunk) + len(r) > limit:
            parts.append(chunk)
            chunk = r
        else:
            chunk += r
    parts.append(chunk)
    return parts


async def send_chunked(message: Message, parts: list[str], reply_markup=None) -> None:
    """Send multiple message parts, attaching keyboard only to the last one."""
    for i, p in enumerate(parts):
        await message.answer(p, reply_markup=reply_markup if i == len(parts) - 1 else None)


from aiogram.methods.base import TelegramMethod
from aiogram.types import Message as AiogramMessage


class _SendRichMessage(TelegramMethod[AiogramMessage]):
    __returning__ = AiogramMessage
    __api_method__ = "sendRichMessage"

    chat_id: int | str
    rich_message: dict[str, Any]
    reply_markup: Any = None


async def send_rich(
    msg: Message,
    markdown: str,
    reply_markup: Any = None,
) -> AiogramMessage:
    payload: dict[str, Any] = {
        "markdown": markdown,
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup.model_dump(exclude_none=True)
    return await msg.bot(
        _SendRichMessage(
            chat_id=msg.chat.id,
            rich_message=payload,
            reply_markup=reply_markup,
        )
    )
