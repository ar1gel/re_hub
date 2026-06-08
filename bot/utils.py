from db.repository import get_ignore_list
from db.models import WbAccount


def filter_by_ignore_list(
    items: list[dict],
    account: WbAccount,
    code_keys: str | list[str] = "vendorCode",
) -> list[dict]:
    ignored = set(get_ignore_list(account))
    if not ignored:
        return items

    if isinstance(code_keys, str):
        code_keys = [code_keys]

    def _is_ignored(item: dict) -> bool:
        for k in code_keys:
            val = item.get(k)
            if val and val in ignored:
                return True
        return False

    return [i for i in items if not _is_ignored(i)]
