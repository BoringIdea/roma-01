"""Trading toolkits for different DEXs and technical analysis."""

from .base_dex import BaseDEXToolkit
from .aster_toolkit import AsterToolkit
from .technical_analysis import TechnicalAnalysisToolkit

try:
    from .hyperliquid_toolkit import HyperliquidToolkit
except ImportError:
    HyperliquidToolkit = None

try:
    from .binance_toolkit import BinanceToolkit
except ImportError:
    BinanceToolkit = None

# Build __all__ based on available toolkits
__all__ = ["BaseDEXToolkit", "AsterToolkit", "TechnicalAnalysisToolkit"]
if HyperliquidToolkit is not None:
    __all__.append("HyperliquidToolkit")
if BinanceToolkit is not None:
    __all__.append("BinanceToolkit")

