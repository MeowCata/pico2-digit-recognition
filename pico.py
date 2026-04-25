import board
import digitalio
import time
import sys
import json
import math
import gc

try:
    with open("pico_mnist_model.json", "r") as f:
        model_data = json.load(f)
        
    HIDDEN_UNITS = model_data["h_units"] # 会加载为 32
    LOGIT_SCALE = model_data["log_s"]
    WEIGHTS1 = model_data["w1"]
    BIASES1 = model_data["b1"]
    W1_SCALE = model_data["w1_s"]
    WEIGHTS2 = model_data["w2"]
    BIASES2 = model_data["b2"]
    W2_SCALE = model_data["w2_s"]
    
    del model_data
    gc.collect()
    
except Exception as e:
    print(json.dumps({"error": "model_import_failed", "detail": str(e)}))
    raise

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT


def blink_led():
    for _ in range(2):
        led.value = True
        time.sleep(0.03)
        led.value = False
        time.sleep(0.03)


def relu(x):
    return x if x > 0.0 else 0.0


def softmax(logits):
    m = logits[0]
    for v in logits[1:]:
        if v > m: m = v
    exps = [math.exp(v - m) for v in logits]
    total = sum(exps)
    if total == 0.0:
        return [0.0 for _ in exps]
    return [e / total for e in exps]


def predict_top2(features):
    hidden = [0.0] * HIDDEN_UNITS
    for i in range(HIDDEN_UNITS):
        acc = BIASES1[i]
        row = WEIGHTS1[i]
        for j in range(784):
            acc += features[j] * (row[j] * W1_SCALE)
        hidden[i] = relu(acc)

    logits = [0.0] * 10
    for i in range(10):
        acc = BIASES2[i]
        row = WEIGHTS2[i]
        for j in range(HIDDEN_UNITS):
            acc += hidden[j] * (row[j] * W2_SCALE)
        logits[i] = acc * LOGIT_SCALE

    probs = softmax(logits)
    
    # 获取置信度最高的两个
    idx_conf = []
    for i in range(10):
        idx_conf.append((i, probs[i] * 100.0))
    
    # 按 Conf 值排序 (降序)
    idx_conf.sort(key=lambda x: x[1], reverse=True)
    
    return idx_conf[0], idx_conf[1]


print("Ready")

while True:
    try:
        line = sys.stdin.readline()
        if not line:
            continue
        line = line.strip()
        if not line:
            continue

        try:
            features = json.loads(line)
        except Exception as e:
            print(json.dumps({"error": "bad_json", "detail": str(e)}))
            continue

        if not isinstance(features, list) or len(features) != 784:
            continue

        blink_led()
        # 核心通信修改：现在返回前两位结果
        best1, best2 = predict_top2(features)
        
        # 返回 JSON 协议更新:
        # {"digit1": 3, "conf1": 98.2, "digit2": 5, "conf2": 1.5}
        print(json.dumps({
            "digit1": best1[0], "conf1": best1[1],
            "digit2": best2[0], "conf2": best2[1]
        }))

    except Exception as e:
        print(json.dumps({"error": str(e)}))