import torch
import torch.nn as nn
import time
import json
from collector import TelemetryCollector

class AnomalyClassifier(nn.Module):
    def __init__(self):
        super(AnomalyClassifier, self).__init__()
        self.fc1 = nn.Linear(5, 16)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(16, 8)
        self.fc3 = nn.Linear(8, 2)  # Output: [0: Normal, 1: Anomaly]

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        return self.fc3(x)

def apply_ptq_quantization(model):
    """Dynamic INT8 dynamic quantization for Linear layers."""
    return torch.ao.quantization.quantize_dynamic(
        model, {nn.Linear}, dtype=torch.qint8
    )

def run_inference():
    collector = TelemetryCollector()
    raw_metrics = collector.capture_metrics()
    input_tensor = collector.extract_features(raw_metrics)

    # Instantiate Baseline & Quantized Models
    fp32_model = AnomalyClassifier()
    fp32_model.eval()

    int8_model = apply_ptq_quantization(fp32_model)

    # FP32 Benchmark
    t0 = time.perf_counter()
    with torch.no_grad():
        out_fp32 = fp32_model(input_tensor)
    fp32_latency = (time.perf_counter() - t0) * 1000

    # INT8 Benchmark
    t1 = time.perf_counter()
    with torch.no_grad():
        out_int8 = int8_model(input_tensor)
    int8_latency = (time.perf_counter() - t1) * 1000

    pred = torch.argmax(out_int8, dim=1).item()

    output = {
        "status": "ANOMALY_DETECTED" if pred == 1 else "HEALTHY",
        "confidence": float(torch.softmax(out_int8, dim=1)[0][pred]),
        "latency_fp32_ms": round(fp32_latency, 4),
        "latency_int8_ms": round(int8_latency, 4),
        "raw_metrics": raw_metrics
    }
    
    # Write output payload for agent orchestrator
    with open("inference_output.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\n--- ON-DEVICE INFERENCE RESULT ---")
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    run_inference()