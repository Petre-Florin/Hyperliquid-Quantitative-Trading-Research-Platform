"""Settings from .env. No hardcoded secrets, ever."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    trading_mode: str = "paper"
    max_exposure_pct: float = 0.20
    max_position_pct_per_symbol: float = 0.05
    min_signal_confidence: float = 0.6
    trade_dollar_amount: float = 100.0
    taker_fee_pct: float = 0.00045
    maker_fee_pct: float = 0.00015
    leverage: float = 5.0