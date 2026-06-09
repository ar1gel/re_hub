from html import escape

from db.repository import get_ignore_list
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
