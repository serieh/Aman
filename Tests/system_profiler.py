# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "psutil",
# ]
# ///

import time
import csv
import psutil
import subprocess
import signal
import sys

# Data storage
metrics_data = []

def get_gpu_metrics():
    try:
        # Get GPU utilization and VRAM usage in MB from nvidia-smi
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used', '--format=csv,noheader,nounits'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output = result.stdout.strip().split(', ')
        if len(output) >= 2:
            gpu_util = float(output[0])
            vram_mb = float(output[1])
            vram_gb = vram_mb / 1024.0
            return gpu_util, vram_gb
    except Exception:
        pass
    return 0.0, 0.0

def signal_handler(sig, frame):
    print("\n\n📊 Profiling stopped! Calculating statistics for your graduation report...")
    if not metrics_data:
        print("No data collected yet. Exiting.")
        sys.exit(0)
        
    cpu_usages = [d['CPU_%'] for d in metrics_data]
    ram_usages = [d['RAM_GB'] for d in metrics_data]
    gpu_usages = [d['GPU_%'] for d in metrics_data]
    vram_usages = [d['VRAM_GB'] for d in metrics_data]
    
    print("-" * 55)
    print("                  📈 AMAN HARDWARE USAGE REPORT")
    print("-" * 55)
    print(f"🖥️  CPU Usage  | Average: {sum(cpu_usages)/len(cpu_usages):6.2f}%  | Peak: {max(cpu_usages):6.2f}%")
    print(f"🧠 RAM Usage  | Average: {sum(ram_usages)/len(ram_usages):6.2f} GB | Peak: {max(ram_usages):6.2f} GB")
    print(f"🎮 GPU Usage  | Average: {sum(gpu_usages)/len(gpu_usages):6.2f}%  | Peak: {max(gpu_usages):6.2f}%")
    print(f"🗄️  VRAM Usage | Average: {sum(vram_usages)/len(vram_usages):6.2f} GB | Peak: {max(vram_usages):6.2f} GB")
    print("-" * 55)
    print(f"✅ Full raw dataset saved to: results/hardware_metrics.csv")
    print("You can open this CSV file in Excel to generate graphs for your report!\n")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(script_dir, "results", "hardware_metrics.csv")
    
    print("🚀 Starting Aman System Profiler...")
    print(f"📝 Logging metrics to '{csv_file}' every 2 seconds.")
    print("⏳ Chat with Aman, run your tests, and press [Ctrl+C] when you are done to generate the final averages!\n")
    
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['Timestamp', 'CPU_%', 'RAM_GB', 'GPU_%', 'VRAM_GB'])
        writer.writeheader()
        
        while True:
            timestamp = time.strftime("%H:%M:%S")
            cpu_percent = psutil.cpu_percent(interval=None)
            ram_gb = psutil.virtual_memory().used / (1024 ** 3)
            gpu_percent, vram_gb = get_gpu_metrics()
            
            data = {
                'Timestamp': timestamp,
                'CPU_%': round(cpu_percent, 2),
                'RAM_GB': round(ram_gb, 2),
                'GPU_%': round(gpu_percent, 2),
                'VRAM_GB': round(vram_gb, 2)
            }
            
            metrics_data.append(data)
            writer.writerow(data)
            file.flush() # Write to disk immediately
            
            print(f"[{timestamp}] CPU: {data['CPU_%']:5.1f}% | RAM: {data['RAM_GB']:5.2f}GB | GPU: {data['GPU_%']:5.1f}% | VRAM: {data['VRAM_GB']:5.2f}GB")
            time.sleep(2)

if __name__ == "__main__":
    # Prime psutil so the first CPU reading isn't 0.0
    psutil.cpu_percent(interval=0.1)
    main()
