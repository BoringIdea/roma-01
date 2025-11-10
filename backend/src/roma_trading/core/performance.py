"""Performance analysis and metrics calculation."""

import numpy as np
from typing import List, Dict
from loguru import logger


class PerformanceAnalyzer:
    """
    Analyzes trading performance and calculates metrics.
    
    Metrics:
    - Win rate
    - Average profit/loss
    - Profit factor
    - Sharpe ratio
    - Maximum drawdown
    """

    @staticmethod
    def calculate_metrics(trades: List[Dict], lookback: int = 20) -> Dict:
        """
        Calculate comprehensive performance metrics.
        
        Args:
            trades: List of completed trades
            lookback: Number of recent trades to analyze
            
        Returns:
            Dict with performance metrics
        """
        if not trades:
            return PerformanceAnalyzer._empty_metrics()
        
        # Use recent trades only
        recent_trades = trades[-lookback:] if len(trades) > lookback else trades
        
        # Separate wins and losses
        profits = [t["pnl_usdt"] for t in recent_trades if t["pnl_usdt"] > 0]
        losses = [abs(t["pnl_usdt"]) for t in recent_trades if t["pnl_usdt"] < 0]
        
        total_trades = len(recent_trades)
        wins = len(profits)
        losses_count = len(losses)
        
        # Win rate
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
        
        # Average profit/loss
        avg_profit = np.mean(profits) if profits else 0.0
        avg_loss = np.mean(losses) if losses else 0.0
        
        # Profit factor
        total_profit = sum(profits) if profits else 0.0
        total_loss = sum(losses) if losses else 0.0
        profit_factor = (total_profit / total_loss) if total_loss > 0 else float('inf')
        
        # Sharpe ratio (risk-adjusted returns)
        returns = [t["pnl_usdt"] for t in recent_trades]
        sharpe_ratio = PerformanceAnalyzer._calculate_sharpe(returns)
        
        # Maximum drawdown
        equity_curve = PerformanceAnalyzer._build_equity_curve(recent_trades, initial=10000.0)
        max_drawdown = PerformanceAnalyzer._calculate_max_drawdown(equity_curve)
        
        # Best and worst trades
        best_trade = max(recent_trades, key=lambda t: t["pnl_usdt"]) if recent_trades else None
        worst_trade = min(recent_trades, key=lambda t: t["pnl_usdt"]) if recent_trades else None
        
        return {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses_count,
            "win_rate": win_rate,
            "avg_profit": avg_profit,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "total_pnl": total_profit - total_loss,
            "best_trade": {
                "symbol": best_trade["symbol"],
                "pnl": best_trade["pnl_usdt"],
            } if best_trade else None,
            "worst_trade": {
                "symbol": worst_trade["symbol"],
                "pnl": worst_trade["pnl_usdt"],
            } if worst_trade else None,
        }

    @staticmethod
    def _calculate_sharpe(returns: List[float], risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            returns: List of returns (USDT)
            risk_free_rate: Risk-free rate (default 0)
            
        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        mean_return = np.mean(returns_array) - risk_free_rate
        std_return = np.std(returns_array)
        
        if std_return == 0:
            return 0.0
        
        return float(mean_return / std_return)

    @staticmethod
    def _build_equity_curve(trades: List[Dict], initial: float = 10000.0) -> List[float]:
        """Build equity curve from trades."""
        equity = [initial]
        
        for trade in trades:
            equity.append(equity[-1] + trade["pnl_usdt"])
        
        return equity

    @staticmethod
    def _calculate_max_drawdown(equity_curve: List[float]) -> float:
        """Calculate maximum drawdown percentage."""
        if len(equity_curve) < 2:
            return 0.0
        
        peak = equity_curve[0]
        max_dd = 0.0
        
        for value in equity_curve[1:]:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak * 100 if peak > 0 else 0.0
            max_dd = max(max_dd, drawdown)
        
        return max_dd

    @staticmethod
    def _empty_metrics() -> Dict:
        """Return empty metrics for no trades."""
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "avg_profit": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "total_pnl": 0.0,
            "best_trade": None,
            "worst_trade": None,
        }

    @staticmethod
    def format_performance(metrics: Dict, language: str = "en") -> str:
        """Format performance metrics for AI prompt."""
        if metrics["total_trades"] == 0:
            return "No trades yet." if language != "zh" else "暂无交易记录。"
        
        if language == "zh":
            lines = [
                f"**绩效概览（{metrics['total_trades']} 笔交易）**",
                f"胜率：{metrics['win_rate']:.1f}%（{metrics['wins']} 胜 / {metrics['losses']} 负）",
                f"平均盈利：${metrics['avg_profit']:.2f} | 平均亏损：${metrics['avg_loss']:.2f}",
                f"收益因子：{metrics['profit_factor']:.2f}",
                f"夏普比率：{metrics['sharpe_ratio']:.2f}",
                f"最大回撤：{metrics['max_drawdown']:.2f}%",
                f"总盈亏：${metrics['total_pnl']:+.2f}",
            ]
            
            if metrics["best_trade"]:
                lines.append(f"最佳交易：{metrics['best_trade']['symbol']} ${metrics['best_trade']['pnl']:+.2f}")
            
            if metrics["worst_trade"]:
                lines.append(f"最差交易：{metrics['worst_trade']['symbol']} ${metrics['worst_trade']['pnl']:+.2f}")
        else:
            lines = [
                f"**Performance Summary ({metrics['total_trades']} trades)**",
                f"Win Rate: {metrics['win_rate']:.1f}% ({metrics['wins']}W / {metrics['losses']}L)",
                f"Avg Profit: ${metrics['avg_profit']:.2f} | Avg Loss: ${metrics['avg_loss']:.2f}",
                f"Profit Factor: {metrics['profit_factor']:.2f}",
                f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}",
                f"Max Drawdown: {metrics['max_drawdown']:.2f}%",
                f"Total P/L: ${metrics['total_pnl']:+.2f}",
            ]
            
            if metrics["best_trade"]:
                lines.append(f"Best: {metrics['best_trade']['symbol']} ${metrics['best_trade']['pnl']:+.2f}")
            
            if metrics["worst_trade"]:
                lines.append(f"Worst: {metrics['worst_trade']['symbol']} ${metrics['worst_trade']['pnl']:+.2f}")
        
        return "\n".join(lines)

