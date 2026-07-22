import asyncio
import logging
import uuid
from typing import TYPE_CHECKING

from hyperliquid.info import Info
from hyperliquid.utils import constants

from client import ExchangeClient
from config import Settings
from events import ExecutionReport, OrderRequest

logger = logging.getLogger("hyperliquid_client")

class HyperliquidClient:
    def __init__(self, settings: Settings) -> None:
        self._info = Info(constants.TESTNET_API_URL, skip_ws=True)
        self._settings = settings

    async def get_price(self, symbol: str) -> float:
        mids = await asyncio.to_thread(self._info.all_mids)
        return float(mids[symbol])

    async def get_orderbook(self, symbol: str) -> dict[str, object]:
        raise NotImplementedError

    async def get_candles(self, symbol: str, interval: str) -> list[dict[str, object]]:
        raise NotImplementedError

    async def place_order(self, order: OrderRequest) -> ExecutionReport:
        if self._settings.trading_mode != "live":
            logger.info(
                "PAPER MODE — would place order: symbol=%s side=%s size=%.6f type=%s",
                order.symbol, order.side, order.size, order.order_type,
            )
            return ExecutionReport(
                order_id=str(uuid.uuid4()),
                symbol=order.symbol,
                status="FILLED",
                filled_size=order.size,
                avg_price=await self.get_price(order.symbol),
            )

        raise NotImplementedError(
            "Live order placement not implemented. Do not flip TRADING_MODE to 'live' "
            "until wallet signing, Phase 9's real-capital DoD, and a week of clean paper "
            "logs are all genuinely satisfied."
        )

    async def cancel_order(self, order_id: str) -> None:
        raise NotImplementedError

if TYPE_CHECKING:
    _: ExchangeClient = HyperliquidClient(Settings())