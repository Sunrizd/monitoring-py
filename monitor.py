import psutil
import json

def get_metrics():

    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory()
    disk_usage = psutil.disk_usage('/')

    metrics = {
            "cpu": {
                "usage_percent": cpu_usage
            },
            "memory": {
                "total_gb": round(memory_usage.total / (1024 ** 3), 2),
                "available_gb": round(memory_usage.available / (1024 ** 3), 2),
                "used_gb": round(memory_usage.used / (1024 ** 3), 2),
                "percent": memory_usage.percent
            },
            "disk": {
                "total_gb": round(disk_usage.total / (1024 ** 3), 2),
                "used_gb": round(disk_usage.used / (1024 ** 3), 2),
                "free_gb": round(disk_usage.free / (1024 ** 3), 2),
                "percent": disk_usage.percent
            }
        }

    return metrics




print("Démarrage de la collecte...")
metrics = get_metrics()
print(json.dumps(metrics, indent=4))