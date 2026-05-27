import os
import time
import random
import logging
import pandas as pd
from datetime import datetime

# =====================================================================
# 0. 日志与全局配置 (Windows 兼容)
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("finance_monitor.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 模拟配置信息，实际开发请放入 config/settings.py
CONFIG = {
    "symbols": ["BTC/USDT", "ETH/USDT", "SPX", "IXIC", "000001.SH"], # 首期监控市场 
    "fetch_interval": 10,       # 监控频率（秒），测试用10秒，生产建议5分钟 [cite: 80]
    "volatility_threshold": 0.02, # 异常波动报警阈值 (2%) [cite: 82]
    "feishu_webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxx" # 飞书机器人接口 [cite: 76, 82]
}

# =====================================================================
# 1. 警报系统模块 (alert/feishu_alert.py)
# =====================================================================
class AlertSystem:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_feishu_alert(self, title, message, level="INFO"):
        """
        触发飞书机器人警报 [cite: 76, 82]。若数据异常或触发高风险，发送红色预警 [cite: 119, 120]。
        """
        color = "red" if level in ["WARNING", "CRITICAL"] else "green"
        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": f"【{level}】{title}",
                        "content": [[{"tag": "text", "text": message}]]
                    }
                }
            }
        }
        # Windows 伪代码提示：实际开发请使用 requests.post(self.webhook_url, json=payload)
        logging.info(f"[飞书播报 - {color.upper()}] 标题: {title} | 内容: {message}")


# =====================================================================
# 2. 数据抓取模块 (data_fetcher/price_fetcher.py)
# =====================================================================
class DataFetcher:
    def __init__(self, symbols):
        self.symbols = symbols

    def fetch_live_prices(self):
        """
        抓取实时行情数据 。
        实际开发周睿需对接 CCXT (加密货币) 或三方财经 API (美股/A股) 。
        """
        try:
            # 模拟抓取当前时间点的价格数据
            mock_data = []
            for symbol in self.symbols:
                # 模拟一个基础价格
                base_price = 65000 if "BTC" in symbol else (3500 if "ETH" in symbol else 4000)
                current_price = base_price * (1 + random.uniform(-0.03, 0.03)) # 模拟波动
                
                mock_data.append({
                    "timestamp": datetime.now(),
                    "symbol": symbol,
                    "price": current_price,
                    "volume": random.uniform(100, 1000)
                })
            return pd.DataFrame(mock_data)
        except Exception as e:
            logging.error(f"数据抓取异常: {e}")
            # 风控硬规则：数据源断开，触发报警，禁止一切策略判断 [cite: 89, 120]
            return None


# =====================================================================
# 3. 指标计算与策略分析模块 (indicators/calculator.py)
# =====================================================================
class FinanceAnalyzer:
    @staticmethod
    def calculate_indicators(df_history):
        """
        根据历史数据计算核心指标：MA、RSI、MACD等 [cite: 76, 83]。
        Windows 环境下推荐使用 pandas 或 pandas-ta 库 。
        """
        # 确保数据按时间排序
        df = df_history.sort_values(by="timestamp")
        
        # 示例：计算简单移动平均线 MA (此处用模拟历史窗口较小时的防错处理)
        if len(df) >= 5:
            df['MA5'] = df['price'].rolling(window=5).mean()
        else:
            df['MA5'] = df['price']
            
        # 实际开发可引入 pandas_ta: df.ta.rsi(close='price', length=14, append=True) 
        df['RSI_mock'] = [random.randint(20, 80) for _ in range(len(df))] 
        return df

    @staticmethod
    def check_risk_rules(current_row, price_change):
        """
        金融风控硬规则审查 [cite: 88, 89]
        """
        # 规则1：波动率异常预警 [cite: 82, 89]
        if abs(price_change) >= CONFIG["volatility_threshold"]:
            return "VOLATILITY_RISK", f"资产 {current_row['symbol']} 波动率达 {price_change:.2%}，触发异常波动报警！"
        
        # 更多硬风控（如单日亏损、连续亏损判断）可在引入模拟盘模块后扩展 [cite: 86, 89]
        return "NORMAL", ""


# =====================================================================
# 4. Windows 主业务循环入口 (main.py)
# =====================================================================
def main():
    logging.info("==== AI 金融数据监控系统 MVP 版本启动 (Windows) ====")
    logging.info("定位：24小时金融监控与辅助决策，绝不承诺稳赚 [cite: 73, 138]。")
    
    # 初始化组件 [cite: 77]
    fetcher = DataFetcher(symbols=CONFIG["symbols"])
    notifier = AlertSystem(webhook_url=CONFIG["feishu_webhook"])
    
    # 模拟本地数据库存储（历史价格池），用于计算指标 
    historical_db = {symbol: pd.DataFrame() for symbol in CONFIG["symbols"]}
    
    try:
        while True:
            logging.info("开始新一轮定时行情抓取...")
            df_current = fetcher.fetch_live_prices()
            
            # 风控硬规则检查：数据异常直接报警不走策略 [cite: 89, 120]
            if df_current is None or df_current.empty:
                notifier.send_feishu_alert("数据源断开异常", "无法获取当前行情数据，系统进入只报警不下单状态！", "CRITICAL")
                time.sleep(CONFIG["fetch_interval"])
                continue
                
            # 分标的进行指标计算与风险监控 [cite: 76, 89]
            for _, row in df_current.iterrows():
                symbol = row["symbol"]
                
                # 更新本地“数据库”
                historical_db[symbol] = pd.concat([historical_db[symbol], pd.DataFrame([row])]).ignore_index=True)
                
                # 保持历史窗口长度，防止内存溢出
                if len(historical_db[symbol]) > 100:
                    historical_db[symbol] = historical_db[symbol].iloc[-100:]
                
                # 计算指标 [cite: 76, 83]
                df_with_indicators = FinanceAnalyzer.calculate_indicators(historical_db[symbol])
                latest_data = df_with_indicators.iloc[-1]
                
                # 计算与上一次价格的涨跌幅
                if len(df_with_indicators) > 1:
                    prev_price = df_with_indicators.iloc[-2]["price"]
                    price_change = (latest_data["price"] - prev_price) / prev_price
                else:
                    price_change = 0.0
                
                # 风控规则过滤 
                risk_status, risk_msg = FinanceAnalyzer.check_risk_rules(latest_data, price_change)
                
                if risk_status != "NORMAL":
                    notifier.send_feishu_alert("风险资产提示", risk_msg, level="WARNING")
                else:
                    logging.info(f"标的: {symbol} | 当前价格: {latest_data['price']:.2f} | MA5: {latest_data['MA5']:.2f} | 状态稳定")
            
            # Windows 线程挂起，等待下一轮循环 [cite: 80]
            logging.info(f"本轮监控结束。等待 {CONFIG['fetch_interval']} 秒后进行下次抓取...\n")
            time.sleep(CONFIG["fetch_interval"])
            
    except KeyboardInterrupt:
        logging.info("检测到 Windows 控制台退出信号，系统安全关闭。")

if __name__ == "__main__":
    main()