#!/usr/bin/env python3
"""
Test Runner for Data Quality Agent
Runs all test files in the tests directory
"""

import os
import sys
import subprocess
import glob
from pathlib import Path

# Add parent directory to path to import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test_file(test_file):
    """Run a single test file"""
    print(f"\n{'='*50}")
    print(f"🧪 Running: {os.path.basename(test_file)}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, 
                              text=True, 
                              timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            print(f"✅ PASSED: {os.path.basename(test_file)}")
            if result.stdout:
                print("Output:", result.stdout[:500])  # Limit output
        else:
            print(f"❌ FAILED: {os.path.basename(test_file)}")
            if result.stderr:
                print("Error:", result.stderr[:500])
                
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: {os.path.basename(test_file)} (5 min limit)")
        return False
    except Exception as e:
        print(f"💥 ERROR: {os.path.basename(test_file)} - {str(e)}")
        return False

def main():
    """Run all tests"""
    test_dir = Path(__file__).parent
    
    print("🚀 Data Quality Agent Test Suite")
    print(f"📁 Test Directory: {test_dir}")
    
    # Find all Python test files
    test_files = list(test_dir.glob("test_*.py")) + list(test_dir.glob("*_test*.py"))
    test_files = [f for f in test_files if f.name != "run_tests.py"]
    
    if not test_files:
        print("❌ No test files found!")
        return
    
    print(f"🔍 Found {len(test_files)} test files")
    
    # Run tests
    passed = 0
    failed = 0
    
    for test_file in sorted(test_files):
        if run_test_file(test_file):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total:  {passed + failed}")
    print(f"🎯 Success Rate: {(passed / (passed + failed) * 100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
