#!/usr/bin/env python3
"""Sidecar pattern — logging, metrics, and health check proxy."""
import time, threading, sys, json

class Sidecar:
    def __init__(self, service_name):
        self.name = service_name; self.logs = []; self.metrics = {}
        self.health = True; self.start_time = time.time()
    def log(self, level, msg):
        entry = {"ts": time.time(), "level": level, "service": self.name, "msg": msg}
        self.logs.append(entry); return entry
    def record_metric(self, name, value):
        if name not in self.metrics: self.metrics[name] = []
        self.metrics[name].append((time.time(), value))
    def health_check(self):
        uptime = time.time() - self.start_time
        return {"service": self.name, "healthy": self.health, "uptime": f"{uptime:.1f}s",
                "log_count": len(self.logs), "metrics": list(self.metrics.keys())}
    def wrap(self, fn, metric_name="call"):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = fn(*args, **kwargs)
                self.record_metric(f"{metric_name}_duration", time.time() - start)
                self.log("INFO", f"{metric_name} succeeded"); return result
            except Exception as e:
                self.record_metric(f"{metric_name}_error", 1)
                self.log("ERROR", f"{metric_name} failed: {e}"); raise
        return wrapper

if __name__ == "__main__":
    sc = Sidecar("order-service")
    process = sc.wrap(lambda x: f"processed-{x}", "process_order")
    for i in range(3): print(process(i))
    sc.log("INFO", "Service running smoothly")
    print(json.dumps(sc.health_check(), indent=2))
