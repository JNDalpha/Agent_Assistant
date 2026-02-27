from langchain.tools import tool
from pydantic import BaseModel, Field
from tradingview_ta import TA_Handler, Interval, Exchange
import traceback

class TradingViewInput(BaseModel):
    symbol: str = Field(..., description="交易对，例如 BTCUSDT 或 AAPL")
    exchange: str = Field(default="BINANCE", description="交易所，例如 BINANCE, NASDAQ")
    screener: str = Field(default="crypto", description="市场类型: crypto, stock, forex")
    interval: str = Field(
        default="1h",
        description="周期: 1m,5m,15m,1h,4h,1d,1W,1M"
    )

INTERVAL_MAP = {
    "1m": Interval.INTERVAL_1_MINUTE,
    "5m": Interval.INTERVAL_5_MINUTES,
    "15m": Interval.INTERVAL_15_MINUTES,
    "1h": Interval.INTERVAL_1_HOUR,
    "4h": Interval.INTERVAL_4_HOURS,
    "1d": Interval.INTERVAL_1_DAY,
    "1W": Interval.INTERVAL_1_WEEK,
    "1M": Interval.INTERVAL_1_MONTH,
}

@tool("get_tradingview_analysis", args_schema=TradingViewInput)
def get_tradingview_analysis(
    symbol: str,
    exchange: str = "BINANCE",
    screener: str = "crypto",
    interval: str = "1h"
):
    """
    获取 TradingView 技术分析数据，包括 RSI、MACD、EMA 和买卖建议，当用户需要检索金融相关内容时调用。
    """

    try:
        handler = TA_Handler(
            symbol=symbol,
            exchange=exchange,
            screener=screener,
            interval=INTERVAL_MAP.get(interval, Interval.INTERVAL_1_HOUR),
        )

        analysis = handler.get_analysis()

        summary = analysis.summary
        indicators = analysis.indicators

        result = f"""
📊 TradingView 技术分析
交易对: {symbol}
交易所: {exchange}
周期: {interval}

🔎 综合建议: {summary.get('RECOMMENDATION')}
🟢 买入: {summary.get('BUY')}
🔴 卖出: {summary.get('SELL')}
⚪ 中立: {summary.get('NEUTRAL')}

📈 关键指标:
RSI: {indicators.get('RSI')}
MACD: {indicators.get('MACD.macd')}
MACD_SIGNAL: {indicators.get('MACD.signal')}
EMA20: {indicators.get('EMA20')}
EMA50: {indicators.get('EMA50')}
EMA200: {indicators.get('EMA200')}
"""
        return result.strip()

    except Exception as e:
        return (
            "❌ 获取 TradingView 数据失败\n"
            f"错误类型: {type(e).__name__}\n"
            f"错误信息: {str(e)}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )