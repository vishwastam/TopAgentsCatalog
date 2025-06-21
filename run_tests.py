#!/usr/bin/env python3
"""
Test runner script for Top Agents Catalog application.
This script provides various options for running tests with different configurations.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description or cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def run_unit_tests():
    """Run unit tests only."""
    return run_command(
        "python3 -m pytest tests/ -v -m 'unit and not slow' --tb=short",
        "Unit Tests (excluding slow tests)"
    )

def run_integration_tests():
    """Run integration tests only."""
    return run_command(
        "python3 -m pytest tests/ -v -m 'integration' --tb=short",
        "Integration Tests"
    )

def run_api_tests():
    """Run API tests only."""
    return run_command(
        "python3 -m pytest tests/ -v -m 'api' --tb=short",
        "API Tests"
    )

def run_ui_tests():
    """Run UI tests only."""
    return run_command(
        "python3 -m pytest tests/ -v -m 'ui' --tb=short",
        "UI Tests"
    )

def run_all_tests():
    """Run all tests."""
    return run_command(
        "python3 -m pytest tests/ -v --tb=short",
        "All Tests"
    )

def run_slow_tests():
    """Run slow tests only."""
    return run_command(
        "python3 -m pytest tests/ -v -m 'slow' --tb=short",
        "Slow Tests"
    )

def run_tests_with_coverage():
    """Run tests with coverage report."""
    return run_command(
        "python3 -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing --tb=short",
        "Tests with Coverage Report"
    )

def run_tests_parallel():
    """Run tests in parallel."""
    return run_command(
        "python3 -m pytest tests/ -v -n auto --tb=short",
        "Tests in Parallel"
    )

def run_specific_test_file(test_file):
    """Run a specific test file."""
    return run_command(
        f"python3 -m pytest {test_file} -v --tb=short",
        f"Specific Test File: {test_file}"
    )

def run_specific_test_class(test_class):
    """Run a specific test class."""
    return run_command(
        f"python3 -m pytest tests/ -v -k {test_class} --tb=short",
        f"Specific Test Class: {test_class}"
    )

def run_specific_test_method(test_method):
    """Run a specific test method."""
    return run_command(
        f"python3 -m pytest tests/ -v -k {test_method} --tb=short",
        f"Specific Test Method: {test_method}"
    )

def run_tests_with_verbose_output():
    """Run tests with verbose output."""
    return run_command(
        "python3 -m pytest tests/ -vvv --tb=long",
        "Tests with Verbose Output"
    )

def run_tests_with_debug():
    """Run tests with debug output."""
    return run_command(
        "python3 -m pytest tests/ -v -s --tb=long",
        "Tests with Debug Output"
    )

def run_tests_failed_only():
    """Run only failed tests from last run."""
    return run_command(
        "python3 -m pytest tests/ -v --lf --tb=short",
        "Failed Tests Only"
    )

def run_tests_new_only():
    """Run only new tests."""
    return run_command(
        "python3 -m pytest tests/ -v --nf --tb=short",
        "New Tests Only"
    )

def check_test_dependencies():
    """Check if all test dependencies are installed."""
    required_packages = [
        'pytest',
        'pytest-cov',
        'pytest-xdist',
        'pytest-html',
        'pytest-mock'
    ]
    
    print("Checking test dependencies...")
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install them with: pip3 install " + " ".join(missing_packages))
        return False
    
    print("\nAll test dependencies are installed!")
    return True

def generate_test_report():
    """Generate an HTML test report."""
    return run_command(
        "python3 -m pytest tests/ -v --html=test_report.html --self-contained-html",
        "Generate HTML Test Report"
    )

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(description='Test runner for Top Agents Catalog')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--api', action='store_true', help='Run API tests only')
    parser.add_argument('--ui', action='store_true', help='Run UI tests only')
    parser.add_argument('--slow', action='store_true', help='Run slow tests only')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--coverage', action='store_true', help='Run tests with coverage')
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('--verbose', action='store_true', help='Run tests with verbose output')
    parser.add_argument('--debug', action='store_true', help='Run tests with debug output')
    parser.add_argument('--failed', action='store_true', help='Run only failed tests')
    parser.add_argument('--new', action='store_true', help='Run only new tests')
    parser.add_argument('--report', action='store_true', help='Generate HTML test report')
    parser.add_argument('--check-deps', action='store_true', help='Check test dependencies')
    parser.add_argument('--file', type=str, help='Run specific test file')
    parser.add_argument('--class', dest='test_class', type=str, help='Run specific test class')
    parser.add_argument('--method', type=str, help='Run specific test method')
    
    args = parser.parse_args()
    
    # Change to project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("Top Agents Catalog - Test Runner")
    print("=" * 50)
    
    success = True
    
    if args.check_deps:
        success = check_test_dependencies()
    elif args.unit:
        success = run_unit_tests()
    elif args.integration:
        success = run_integration_tests()
    elif args.api:
        success = run_api_tests()
    elif args.ui:
        success = run_ui_tests()
    elif args.slow:
        success = run_slow_tests()
    elif args.coverage:
        success = run_tests_with_coverage()
    elif args.parallel:
        success = run_tests_parallel()
    elif args.verbose:
        success = run_tests_with_verbose_output()
    elif args.debug:
        success = run_tests_with_debug()
    elif args.failed:
        success = run_tests_failed_only()
    elif args.new:
        success = run_tests_new_only()
    elif args.report:
        success = generate_test_report()
    elif args.file:
        success = run_specific_test_file(args.file)
    elif args.test_class:
        success = run_specific_test_class(args.test_class)
    elif args.method:
        success = run_specific_test_method(args.method)
    elif args.all:
        success = run_all_tests()
    else:
        # Default: run all tests
        print("No specific test type specified. Running all tests...")
        success = run_all_tests()
    
    if success:
        print("\n" + "="*60)
        print("✅ All tests completed successfully!")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ Some tests failed!")
        print("="*60)
        sys.exit(1)

if __name__ == '__main__':
    main() 