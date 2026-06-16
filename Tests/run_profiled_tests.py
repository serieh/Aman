import subprocess
import time
import os
import signal
import sys

def main():
    print("🚀 Starting Automated Profiled Test Run...")
    
    # Paths
    cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    profiler_path = os.path.join(cwd, "Tests", "system_profiler.py")
    scenarios_path = os.path.join(cwd, "Tests", "integration_scenarios.py")
    
    # 1. Start the system profiler in the background
    print(f"📋 Starting system profiler: {profiler_path}")
    profiler_proc = subprocess.Popen(
        ["uv", "run", profiler_path],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Give the profiler a moment to initialize
    time.sleep(3)
    
    # 2. Run the integration scenarios
    print(f"🏃 Running integration scenarios: {scenarios_path}")
    scenarios_proc = subprocess.run(
        ["uv", "run", "python", scenarios_path],
        cwd=cwd,
        capture_output=True,
        text=True
    )
    
    print("Integration scenarios completed. Output:")
    print(scenarios_proc.stdout)
    if scenarios_proc.stderr:
        print("Errors:")
        print(scenarios_proc.stderr)
        
    # 3. Terminate the system profiler cleanly
    print("🛑 Terminating system profiler to compile report...")
    profiler_proc.send_signal(signal.SIGTERM)
    
    # Wait for the profiler to finish writing and exit
    try:
        stdout, stderr = profiler_proc.communicate(timeout=10)
        print("\n=======================================================")
        print("📊 SYSTEM PROFILER REPORT:")
        print("=======================================================")
        print(stdout)
        if stderr:
            print("Profiler Errors:")
            print(stderr)
    except subprocess.TimeoutExpired:
        print("Profiler failed to terminate in time. Killing it.")
        profiler_proc.kill()
        
    print("🎉 Profiled test run complete!")

if __name__ == "__main__":
    main()
