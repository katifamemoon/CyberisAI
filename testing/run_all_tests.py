#!/usr/bin/env python3
"""
Test runner script for the AI Safety Detection System.
This script runs all tests in the testing directory.
"""

import unittest
import os
import sys

def run_tests():
    """Discover and run all tests"""
    # Add the current directory to the path so we can import test modules
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    # Create a test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Discover tests in api_endpoints directory
    api_tests_dir = os.path.join(os.path.dirname(__file__), 'api_endpoints')
    if os.path.exists(api_tests_dir):
        api_suite = loader.discover(api_tests_dir, pattern='test_*.py')
        suite.addTest(api_suite)
    
    # Discover tests in model_testing directory
    model_tests_dir = os.path.join(os.path.dirname(__file__), 'model_testing')
    if os.path.exists(model_tests_dir):
        model_suite = loader.discover(model_tests_dir, pattern='test_*.py')
        suite.addTest(model_suite)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)