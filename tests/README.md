# Test Suite Documentation

This directory contains comprehensive test cases for the Top Agents Catalog Flask application.

## Test Structure

### Test Files

- `test_routes.py` - Main test file containing all route and page tests
- `test_idp_discovery.py` - Tests for IDP discovery functionality
- `conftest.py` - Pytest configuration and shared fixtures

### Test Categories

The test suite is organized into the following categories:

#### 1. Main Routes (`TestMainRoutes`)
Tests for all main application routes:
- Homepage and landing pages
- Agent listing and detail pages
- Recipe pages
- Blog pages
- Authentication pages
- Dashboard and admin pages
- Form submissions and data processing

#### 2. API Routes (`TestAPIRoutes`)
Tests for all API endpoints:
- Agent search and detail APIs
- Category and recipe APIs
- Search functionality
- OpenAPI specification
- Blog post APIs

#### 3. Discovery Routes (`TestDiscoveryRoutes`)
Tests for IDP discovery functionality:
- Google Workspace IDP registration
- App catalog fetching
- Error handling and validation

#### 4. Error Handlers (`TestErrorHandlers`)
Tests for error handling:
- 404 error pages
- 500 error pages
- Custom error responses

#### 5. Authentication Routes (`TestAuthenticationRoutes`)
Tests for authentication:
- Google OAuth integration
- Session management
- User authentication flows

#### 6. Template Rendering (`TestTemplateRendering`)
Tests for template functionality:
- Base template structure
- Navigation elements
- Meta tags and SEO elements

#### 7. Data Loading (`TestDataLoading`)
Tests for data loading:
- Agent data loading
- Recipe data loading
- Blog data loading

#### 8. Search Functionality (`TestSearchFunctionality`)
Tests for search features:
- Text search
- Filter combinations
- API search endpoints

#### 9. Edge Cases (`TestEdgeCases`)
Tests for edge cases:
- Empty queries
- Special characters
- Invalid slugs
- Large inputs

#### 10. Form Validation (`TestFormValidation`)
Tests for form validation:
- Login form validation
- Signup form validation
- Demo request validation
- Agent submission validation

#### 11. API Parameters (`TestAPIParameters`)
Tests for API parameter handling:
- Invalid parameters
- Parameter validation
- Filter combinations

#### 12. Content Types (`TestContentTypes`)
Tests for content type handling:
- JSON API responses
- XML endpoints
- Text endpoints

#### 13. Redirects (`TestRedirects`)
Tests for redirect functionality:
- Old URL format redirects
- Search redirects
- Filter redirects

#### 14. Session Handling (`TestSessionHandling`)
Tests for session management:
- Session creation
- Session clearing
- Authentication state

#### 15. Security (`TestSecurity`)
Tests for security features:
- CSRF protection
- SQL injection protection
- XSS protection

#### 16. Performance (`TestPerformance`)
Tests for performance:
- Page load times
- API response times
- Performance benchmarks

#### 17. SEO (`TestSEO`)
Tests for SEO features:
- Meta descriptions
- Open Graph tags
- Canonical URLs
- Structured data

#### 18. Accessibility (`TestAccessibility`)
Tests for accessibility:
- Alt text on images
- Semantic HTML structure
- ARIA attributes

#### 19. Mobile Responsiveness (`TestMobileResponsiveness`)
Tests for mobile features:
- Viewport meta tags
- Responsive CSS classes
- Mobile-specific functionality

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r test_requirements.txt
```

### Basic Test Commands

Run all tests:
```bash
python -m pytest tests/
```

Run with verbose output:
```bash
python -m pytest tests/ -v
```

Run specific test categories:
```bash
# Unit tests only
python -m pytest tests/ -m "unit and not slow"

# API tests only
python -m pytest tests/ -m "api"

# UI tests only
python -m pytest tests/ -m "ui"

# Integration tests only
python -m pytest tests/ -m "integration"
```

### Using the Test Runner Script

The `run_tests.py` script provides convenient options:

```bash
# Run all tests
python run_tests.py --all

# Run unit tests only
python run_tests.py --unit

# Run with coverage
python run_tests.py --coverage

# Run in parallel
python run_tests.py --parallel

# Generate HTML report
python run_tests.py --report

# Check dependencies
python run_tests.py --check-deps

# Run specific test file
python run_tests.py --file tests/test_routes.py

# Run specific test class
python run_tests.py --class TestMainRoutes

# Run specific test method
python run_tests.py --method test_homepage_get
```

### Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.api` - API tests
- `@pytest.mark.ui` - UI tests
- `@pytest.mark.slow` - Slow tests (performance, etc.)

Run tests excluding slow ones:
```bash
python -m pytest tests/ -m "not slow"
```

## Test Configuration

### Fixtures

The `conftest.py` file provides shared fixtures:

- `app` - Flask application instance
- `client` - Test client
- `runner` - CLI test runner
- `mock_data_files` - Mock CSV data files
- `mock_blog_files` - Mock blog markdown files
- `mock_user_data` - Mock user data
- `mock_google_credentials` - Mock Google credentials
- `mock_external_services` - Mock external API calls

### Environment Variables

Tests use the following environment variables:
- `TESTING=True` - Enables test mode
- `WTF_CSRF_ENABLED=False` - Disables CSRF for testing

### Database

Tests use an in-memory SQLite database that is created and destroyed for each test session.

## Test Data

### Mock Data Files

The test suite includes mock data files:
- `combined_ai_agents_directory.csv` - Sample agent data
- `recipes_full_content.csv` - Sample recipe data
- Blog markdown files - Sample blog posts

### Mock External Services

External services are mocked to avoid real API calls:
- Google APIs
- Authentication services
- External HTTP requests

## Coverage

Generate coverage reports:
```bash
python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing
```

This generates:
- HTML coverage report in `htmlcov/`
- Terminal coverage summary
- Missing line coverage information

## Continuous Integration

### GitHub Actions

The test suite can be integrated with GitHub Actions:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r test_requirements.txt
    - name: Run tests
      run: python run_tests.py --coverage
```

### Pre-commit Hooks

Install pre-commit hooks for automatic testing:

```bash
pip install pre-commit
pre-commit install
```

## Best Practices

### Writing Tests

1. **Test Naming**: Use descriptive test names that explain what is being tested
2. **Arrange-Act-Assert**: Structure tests with clear sections
3. **Mocking**: Mock external dependencies to isolate units under test
4. **Fixtures**: Use fixtures for common setup and teardown
5. **Edge Cases**: Test edge cases and error conditions
6. **Performance**: Include performance tests for critical paths

### Test Organization

1. **Group Related Tests**: Use test classes to group related functionality
2. **Use Markers**: Mark tests appropriately for selective execution
3. **Keep Tests Independent**: Each test should be independent of others
4. **Clean Up**: Ensure proper cleanup in fixtures and teardown

### Debugging Tests

Run tests with debug output:
```bash
python -m pytest tests/ -v -s --tb=long
```

Run specific failing tests:
```bash
python -m pytest tests/ -v -k "test_name"
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in the Python path
2. **Database Issues**: Check that the test database is properly configured
3. **Mock Issues**: Verify that external services are properly mocked
4. **Environment Issues**: Ensure all required environment variables are set

### Debugging Tips

1. Use `pytest -s` to see print statements
2. Use `pytest --tb=long` for detailed tracebacks
3. Use `pytest -x` to stop on first failure
4. Use `pytest --lf` to run only failed tests

## Performance Testing

### Load Testing

For load testing, use Locust:
```bash
locust -f tests/locustfile.py
```

### Benchmark Testing

For benchmark testing, use pytest-benchmark:
```bash
python -m pytest tests/ --benchmark-only
```

## Security Testing

### Static Analysis

Run security checks:
```bash
bandit -r .
```

### Dependency Scanning

Check for vulnerable dependencies:
```bash
safety check
```

## Contributing

When adding new tests:

1. Follow the existing test structure
2. Use appropriate markers
3. Add comprehensive docstrings
4. Include edge cases and error conditions
5. Update this documentation if needed

## Test Metrics

Track test metrics over time:
- Test coverage percentage
- Test execution time
- Number of tests
- Test categories distribution
- Failure rates

Use the test runner script to generate reports and track these metrics. 