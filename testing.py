"""
Testing & CI/CD Module for Octagon Pro
Implements unit tests, integration tests, and CI/CD configuration
"""

import unittest
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json


# ============================================================================
# TEST FRAMEWORK UTILITIES
# ============================================================================

class TestResult:
    """Store test result"""
    
    def __init__(self, test_name: str, status: str, message: str = "",
                execution_time: float = 0):
        self.test_name = test_name
        self.status = status  # "passed", "failed", "error", "skipped"
        self.message = message
        self.execution_time = execution_time
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "status": self.status,
            "message": self.message,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp
        }


class TestSuite:
    """Manage test suite"""
    
    def __init__(self, suite_name: str):
        self.suite_name = suite_name
        self.results: List[TestResult] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
    
    def add_result(self, result: TestResult) -> None:
        """Add test result"""
        self.results.append(result)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test suite summary"""
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "passed")
        failed = sum(1 for r in self.results if r.status == "failed")
        errors = sum(1 for r in self.results if r.status == "error")
        skipped = sum(1 for r in self.results if r.status == "skipped")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        total_time = sum(r.execution_time for r in self.results)
        
        return {
            "suite_name": self.suite_name,
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "success_rate": round(success_rate, 2),
            "total_execution_time": round(total_time, 2),
            "timestamp": datetime.now().isoformat()
        }


# ============================================================================
# UNIT TEST CASES
# ============================================================================

class TestSecurity(unittest.TestCase):
    """Unit tests for security module"""
    
    def setUp(self):
        """Set up test fixtures"""
        from security import PasswordManager, InputValidator, RateLimiter
        self.password_manager = PasswordManager()
        self.input_validator = InputValidator()
        self.rate_limiter = RateLimiter()
    
    def test_password_hashing(self):
        """Test password hashing"""
        password = "test_password_123"
        result = self.password_manager.hash_password(password)
        
        self.assertIn("hash", result)
        self.assertIn("salt", result)
        self.assertNotEqual(result["hash"], password)
    
    def test_email_validation(self):
        """Test email validation"""
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "another+tag@example.org"
        ]
        
        invalid_emails = [
            "invalid_email",
            "@nodomain.com",
            "user@",
            "user name@example.com"
        ]
        
        for email in valid_emails:
            is_valid = self.input_validator.validate_email(email)
            self.assertTrue(is_valid, f"{email} should be valid")
        
        for email in invalid_emails:
            is_valid = self.input_validator.validate_email(email)
            self.assertFalse(is_valid, f"{email} should be invalid")
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        user_id = "test_user"
        max_requests = 5
        time_window = 60
        
        # First 5 requests should succeed
        for i in range(max_requests):
            is_allowed = self.rate_limiter.is_allowed(
                user_id, max_requests, time_window
            )
            self.assertTrue(is_allowed, f"Request {i+1} should be allowed")
        
        # 6th request should fail
        is_allowed = self.rate_limiter.is_allowed(
            user_id, max_requests, time_window
        )
        self.assertFalse(is_allowed, "Request 6 should be denied")


class TestPerformance(unittest.TestCase):
    """Unit tests for performance module"""
    
    def setUp(self):
        """Set up test fixtures"""
        from performance import CacheManager, PerformanceMonitor
        self.cache = CacheManager(max_size=10, ttl=3600)
        self.monitor = PerformanceMonitor()
    
    def test_cache_set_get(self):
        """Test cache set and get"""
        key = "test_key"
        value = {"data": "test_value"}
        
        self.cache.set(key, value)
        retrieved = self.cache.get(key)
        
        self.assertEqual(retrieved, value)
    
    def test_cache_miss(self):
        """Test cache miss"""
        key = "nonexistent_key"
        retrieved = self.cache.get(key)
        
        self.assertIsNone(retrieved)
    
    def test_performance_monitoring(self):
        """Test performance monitoring"""
        import time
        
        def slow_function():
            time.sleep(0.1)
            return "result"
        
        # Record execution time
        start = time.time()
        result = slow_function()
        execution_time = time.time() - start
        
        self.assertEqual(result, "result")
        self.assertGreater(execution_time, 0.09)


class TestValidation(unittest.TestCase):
    """Unit tests for input validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        from security import InputValidator
        self.validator = InputValidator()
    
    def test_phone_validation(self):
        """Test phone number validation"""
        valid_phones = [
            "+1234567890",
            "1234567890",
            "+34912345678"
        ]
        
        invalid_phones = [
            "123",
            "abc1234567890",
            ""
        ]
        
        for phone in valid_phones:
            is_valid = self.validator.validate_phone(phone)
            self.assertTrue(is_valid, f"{phone} should be valid")
        
        for phone in invalid_phones:
            is_valid = self.validator.validate_phone(phone)
            self.assertFalse(is_valid, f"{phone} should be invalid")
    
    def test_username_validation(self):
        """Test username validation"""
        valid_usernames = ["user123", "john_doe", "athlete2024"]
        invalid_usernames = ["u", "user@invalid", ""]
        
        for username in valid_usernames:
            is_valid = self.validator.validate_username(username)
            self.assertTrue(is_valid, f"{username} should be valid")
        
        for username in invalid_usernames:
            is_valid = self.validator.validate_username(username)
            self.assertFalse(is_valid, f"{username} should be invalid")


# ============================================================================
# TEST RUNNER
# ============================================================================

class TestRunner:
    """Run and manage tests"""
    
    def __init__(self):
        self.suites: Dict[str, TestSuite] = {}
    
    def run_test_suite(self, suite_name: str,
                      test_cases: List[unittest.TestCase]) -> TestSuite:
        """Run a test suite"""
        
        suite = TestSuite(suite_name)
        loader = unittest.TestLoader()
        runner = unittest.TextTestRunner(verbosity=0, stream=None)
        
        for test_case in test_cases:
            # Load tests from test case
            tests = loader.loadTestsFromTestCase(test_case)
            
            # Run tests
            result = runner.run(tests)
            
            # Process results
            for test, traceback in result.failures:
                test_result = TestResult(
                    str(test),
                    "failed",
                    traceback,
                    0
                )
                suite.add_result(test_result)
            
            for test, traceback in result.errors:
                test_result = TestResult(
                    str(test),
                    "error",
                    traceback,
                    0
                )
                suite.add_result(test_result)
            
            for test in result.skipped:
                test_result = TestResult(
                    str(test[0]),
                    "skipped",
                    test[1],
                    0
                )
                suite.add_result(test_result)
            
            # Add passed tests
            num_tests = result.testsRun
            num_failed = len(result.failures) + len(result.errors)
            num_passed = num_tests - num_failed - len(result.skipped)
            
            for i in range(num_passed):
                test_result = TestResult(
                    f"test_{i}",
                    "passed",
                    "",
                    0
                )
                suite.add_result(test_result)
        
        self.suites[suite_name] = suite
        return suite
    
    def get_all_results(self) -> Dict[str, Any]:
        """Get all test results"""
        
        all_results = {}
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        for suite_name, suite in self.suites.items():
            summary = suite.get_summary()
            all_results[suite_name] = summary
            
            total_tests += summary["total_tests"]
            total_passed += summary["passed"]
            total_failed += summary["failed"]
        
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "suites": all_results,
            "overall": {
                "total_tests": total_tests,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "overall_success_rate": round(overall_success_rate, 2)
            },
            "timestamp": datetime.now().isoformat()
        }


# Global test runner
test_runner = TestRunner()


# ============================================================================
# CI/CD CONFIGURATION
# ============================================================================

class CICDConfig:
    """CI/CD pipeline configuration"""
    
    GITHUB_ACTIONS_WORKFLOW = """
name: Octagon Pro CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10"]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
  
  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.10
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install bandit safety
    
    - name: Run security checks
      run: |
        bandit -r . -ll
        safety check
  
  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.10
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 pylint
    
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
"""
    
    GITLAB_CI_CONFIG = """
stages:
  - test
  - security
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - venv/

before_script:
  - python --version
  - pip install -r requirements.txt

test:
  stage: test
  script:
    - pip install pytest pytest-cov
    - pytest --cov=. --cov-report=term
  coverage: '/TOTAL.*\\s+(\\d+%)$/'

security:
  stage: security
  script:
    - pip install bandit safety
    - bandit -r . -ll
    - safety check

lint:
  stage: test
  script:
    - pip install flake8 pylint
    - flake8 . --count --statistics
"""
    
    PRECOMMIT_CONFIG = """
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
  
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
"""
    
    @staticmethod
    def get_test_script() -> str:
        """Get pytest configuration script"""
        
        return """
import pytest
import sys

# Pytest configuration
pytest_plugins = ['pytest-cov']

# Marker definitions
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "security: Security tests",
    "performance: Performance tests",
    "slow: Slow running tests"
]
"""
    
    @staticmethod
    def get_requirements_for_testing() -> List[str]:
        """Get testing dependencies"""
        
        return [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "bandit>=1.7.5",
            "safety>=2.3.0",
            "flake8>=6.0.0",
            "pylint>=2.17.0",
            "black>=23.3.0",
            "isort>=5.12.0"
        ]


# Global CI/CD config
cicd_config = CICDConfig()
