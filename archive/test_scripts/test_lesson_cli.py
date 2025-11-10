#!/usr/bin/env python3

import subprocess
import sys

# Test the lesson generation CLI with automated input
input_text = "1\n1\n1\nrhythm\nbeginner\n30\nyes\nlesson.md\n"

try:
    process = subprocess.run(
        [sys.executable, "-m", "cli.main", "generate", "lesson"],
        input=input_text,
        text=True,
        capture_output=True,
        timeout=30
    )
    
    print("=== STDOUT ===")
    print(process.stdout)
    print("\n=== STDERR ===") 
    print(process.stderr)
    print(f"\n=== Return code: {process.returncode} ===")
    
except subprocess.TimeoutExpired:
    print("Process timed out - this is expected as it's waiting for LLM responses")
except Exception as e:
    print(f"Error: {e}")