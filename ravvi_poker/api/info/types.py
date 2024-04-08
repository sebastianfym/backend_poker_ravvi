from pydantic import BaseModel


class TimeZoneInput(BaseModel):
    timezone_user: str | None


class TxnHistoryManual(BaseModel):
    username: str | None
    sender_id: int | None
    txn_time: float | None
    txn_type: str | None
    txn_value: float | None
    balance: float | None
    image_id: int | None = None
    role: str | None


class TxnHistoryOnTable(BaseModel):
    username: str | None = None
    table_name: str | None
    table_id: int | None
    txn_time: float | None
    min_blind: float | None
    max_blind: float | None
    txn_type: str | None
    txn_value: float | None
    balance: float | None