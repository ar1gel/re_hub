_state: dict[int, str] = {}
_selected_account: dict[int, int] = {}


def set_menu(user_id: int, menu: str) -> None:
    _state[user_id] = menu


def get_menu(user_id: int) -> str:
    return _state.get(user_id, "main")


def set_account(user_id: int, account_id: int) -> None:
    _selected_account[user_id] = account_id


def get_account(user_id: int) -> int | None:
    return _selected_account.get(user_id)
