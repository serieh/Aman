import os
import json
import csv
import numpy as np
import matplotlib.pyplot as plt

def main():
    print("🚀 Starting automated chart generation using matplotlib...")
    
    # Paths
    cwd = os.path.abspath(os.path.dirname(__file__))
    hardware_csv = os.path.join(cwd, "results", "hardware_metrics.csv")
    eval_json = os.path.join(cwd, "results", "evaluation_summary.json")
    
    # ── 1. Render Hardware Utilization Line Charts ──────────────────────────────
    if os.path.exists(hardware_csv):
        print(f"Reading hardware metrics from {hardware_csv}...")
        timestamps = []
        cpu = []
        ram = []
        gpu = []
        vram = []
        
        with open(hardware_csv, mode='r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                timestamps.append(row['Timestamp'])
                cpu.append(float(row['CPU_%']))
                ram.append(float(row['RAM_GB']))
                gpu.append(float(row['GPU_%']))
                vram.append(float(row['VRAM_GB']))
        
        # Plot 2x2 subplots for clarity
        fig, axs = plt.subplots(2, 2, figsize=(14, 10))
        
        # CPU
        axs[0, 0].plot(cpu, color='#1f77b4', linewidth=2)
        axs[0, 0].set_title('CPU Utilization (%)', fontsize=12, fontweight='bold')
        axs[0, 0].set_ylabel('CPU %')
        axs[0, 0].grid(True, linestyle='--', alpha=0.6)
        
        # RAM
        axs[0, 1].plot(ram, color='#ff7f0e', linewidth=2)
        axs[0, 1].set_title('RAM Usage (GB)', fontsize=12, fontweight='bold')
        axs[0, 1].set_ylabel('RAM GB')
        axs[0, 1].grid(True, linestyle='--', alpha=0.6)
        
        # GPU
        axs[1, 0].plot(gpu, color='#2ca02c', linewidth=2)
        axs[1, 0].set_title('GPU Utilization (%)', fontsize=12, fontweight='bold')
        axs[1, 0].set_ylabel('GPU %')
        axs[1, 0].grid(True, linestyle='--', alpha=0.6)
        
        # VRAM
        axs[1, 1].plot(vram, color='#d62728', linewidth=2)
        axs[1, 1].set_title('VRAM Allocation (GB)', fontsize=12, fontweight='bold')
        axs[1, 1].set_ylabel('VRAM GB')
        axs[1, 1].grid(True, linestyle='--', alpha=0.6)
        
        plt.suptitle('Aman AI System Resource Profile (Local Hardware Run)', fontsize=16, fontweight='bold')
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        hardware_out = os.path.join(cwd, "results", "hardware_utilization.png")
        plt.savefig(hardware_out, dpi=300)
        plt.close()
        print(f"Saved: {hardware_out}")
    else:
        print(f"Warning: {hardware_csv} not found. Skipping hardware chart.")
        
    # ── 2. Render Safety Firewall Confusion Matrix Heatmap ────────────────────────
    if os.path.exists(eval_json):
        print(f"Reading evaluation summary from {eval_json}...")
        with open(eval_json, 'r') as f:
            data = json.load(f)
            
        stats = data.get("overall_stats", {})
        cm = stats.get("confusion_matrix", {})
        
        # Build 3x3 matrix (Ground Truth rows vs Classified columns)
        # Order: RED, GRAY, SAFE
        matrix = np.array([
            [cm.get("RED_RED", 0), cm.get("RED_GRAY", 0), cm.get("RED_SAFE", 0)],
            [cm.get("GRAY_RED", 0), cm.get("GRAY_GRAY", 0), cm.get("GRAY_SAFE", 0)],
            [cm.get("SAFE_RED", 0), cm.get("SAFE_GRAY", 0), cm.get("SAFE_SAFE", 0)]
        ])
        
        fig, ax = plt.subplots(figsize=(8, 6))
        cax = ax.matshow(matrix, cmap=plt.cm.Blues)
        fig.colorbar(cax)
        
        # Tick marks
        labels = ['RED', 'GRAY', 'SAFE']
        ax.set_xticks([0, 1, 2])
        ax.set_yticks([0, 1, 2])
        ax.set_xticklabels(labels, fontsize=11, fontweight='bold')
        ax.set_yticklabels(labels, fontsize=11, fontweight='bold')
        
        # Text inside cells
        for i in range(3):
            for j in range(3):
                ax.text(j, i, str(matrix[i, j]), va='center', ha='center', fontsize=14, fontweight='bold',
                        color="white" if matrix[i, j] > (matrix.max() / 2) else "black")
                        
        plt.title('Aman AI Safety Input Firewall Confusion Matrix', fontsize=14, fontweight='bold', pad=20)
        plt.xlabel('System Classified Flag', fontsize=12, fontweight='bold')
        plt.ylabel('Ground Truth Flag', fontsize=12, fontweight='bold')
        
        cm_out = os.path.join(cwd, "results", "safety_confusion_matrix.png")
        plt.savefig(cm_out, dpi=300)
        plt.close()
        print(f"Saved: {cm_out}")
        
        # ── 3. Render Latency Breakdown Bar Chart ────────────────────────────────
        avg_latencies = stats.get("averages", {})
        
        stages = ['Input Safety Firewall', 'RAG Vector Search', 'LLM Stream (TTFT)', 'Total Response Latency']
        # Est. TTFT as Total Latency minus Safety and RAG search times
        input_saf = avg_latencies.get("input_safety_ms", 0.0)
        rag_search = avg_latencies.get("rag_retrieval_ms", 0.0)
        total_lat = avg_latencies.get("overall_latency_ms", 0.0)
        llm_ttft = avg_latencies.get("llm_ttft_ms")
        if llm_ttft is None:
            llm_ttft = max(0.0, total_lat - input_saf - rag_search)
        
        times = [input_saf, rag_search, llm_ttft, total_lat]
        
        plt.figure(figsize=(10, 6))
        colors = ['#1f77b4', '#aec7e8', '#ffbb78', '#ff7f0e']
        bars = plt.barh(stages, times, color=colors, edgecolor='grey', height=0.6)
        
        plt.xlabel('Latency (Milliseconds)', fontsize=12, fontweight='bold')
        plt.title('Aman AI Core Operation Latency Breakdown (Averages)', fontsize=14, fontweight='bold')
        plt.grid(axis='x', linestyle='--', alpha=0.6)
        
        # Add labels to bars
        for bar in bars:
            width = bar.get_width()
            plt.text(width + 15, bar.get_y() + bar.get_height()/2, f'{width:.1f} ms', 
                     va='center', ha='left', fontsize=11, fontweight='bold')
                     
        plt.tight_layout()
        latency_out = os.path.join(cwd, "results", "latency_breakdown.png")
        plt.savefig(latency_out, dpi=300)
        plt.close()
        print(f"Saved: {latency_out}")
        
        # ── 4. Render Alignment Grading Stacked Bar Chart ──────────────────────────
        percentages = stats.get("grades_percentages", {})
        
        categories = ['Empathy & Active Listening', 'Safety & Boundaries Check', 'Grounding & Relevance']
        yes_vals = [percentages.get("empathy", {}).get("Yes", 0.0), percentages.get("safety", {}).get("Yes", 0.0), percentages.get("grounding", {}).get("Yes", 0.0)]
        no_vals = [percentages.get("empathy", {}).get("No", 0.0), percentages.get("safety", {}).get("No", 0.0), percentages.get("grounding", {}).get("No", 0.0)]
        unc_vals = [percentages.get("empathy", {}).get("Uncertain", 0.0), percentages.get("safety", {}).get("Uncertain", 0.0), percentages.get("grounding", {}).get("Uncertain", 0.0)]
        
        x = np.arange(len(categories))
        width = 0.25
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        rects1 = ax.bar(x - width, yes_vals, width, label='Yes (Achieved)', color='#2ca02c')
        rects2 = ax.bar(x, no_vals, width, label='No (Discrepancy)', color='#d62728')
        rects3 = ax.bar(x + width, unc_vals, width, label='Uncertain / Neutral', color='#7f7f7f')
        
        ax.set_ylabel('Percentage of Queries (%)', fontsize=12, fontweight='bold')
        ax.set_title('Aman AI System Alignment and QA Performance Summary', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=11, fontweight='bold')
        ax.set_ylim(0, 115)
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.6)
        
        # Add labels on top of bars
        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                ax.annotate(f'{height:.1f}%',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=9, fontweight='bold')
                            
        autolabel(rects1)
        autolabel(rects2)
        autolabel(rects3)
        
        plt.tight_layout()
        alignment_out = os.path.join(cwd, "results", "system_qa_alignment.png")
        plt.savefig(alignment_out, dpi=300)
        plt.close()
        print(f"Saved: {alignment_out}")
        
    else:
        print(f"Warning: {eval_json} not found. Skipping evaluation charts.")
        
    print("🎉 Chart generation complete!")

if __name__ == "__main__":
    main()
