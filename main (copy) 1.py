from flask import Flask, request, jsonify
from data_router import fetch_data   # ← 原来写成 core.data_router 会报错
from core.signal_engine import generate_signal
from utils.formatter import format_signal_output
from utils.logger import log_event
from utils.archiver import archive_signal
from push.telegram_push import send_telegram
from data.training_data_builder import (
    generate_training_sample,
    generate_training_sample_json
)

app = Flask(__name__)

def run(mode="real", symbol="ETH", screenshot_path=None, date_str=None):
    log_event(f"[MAIN] 运行模式: {mode}, 币种: {symbol}")

    raw_data = fetch_data(
        mode=mode,
        symbol=symbol,
        screenshot_path=screenshot_path,
        date=date_str
    )

    signal = generate_signal(symbol, raw_data)
    if not signal:
        log_event("[MAIN] 无法生成信号")
        return None

    output = format_signal_output(signal)
    print(output)
    log_event("[MAIN] 输出完成")

    send_telegram(output)
    archive_signal(symbol, output)
    generate_training_sample(signal)
    generate_training_sample_json(signal)

    return output

# ✅ Web 接口触发（POST /trigger）
@app.route("/trigger", methods=["POST"])
def trigger():
    data = request.json or {}
    symbol = data.get("symbol", "ETH").upper()
    screenshot_path = data.get("screenshot_path")
    date_str = data.get("date")
    mode = data.get("mode", "real")

    output = run(mode=mode, symbol=symbol, screenshot_path=screenshot_path, date_str=date_str)

    return jsonify({
        "status": "ok" if output else "fail",
        "symbol": symbol,
        "output": output or "❌ 无法生成信号"
    })

# ✅ 启动服务
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)