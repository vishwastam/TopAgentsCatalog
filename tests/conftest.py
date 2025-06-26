import pytest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="session")
def mock_data_files(test_data_dir):
    """Create mock data files for testing."""
    # Create mock CSV files
    agents_csv = os.path.join(test_data_dir, "combined_ai_agents_directory.csv")
    recipes_csv = os.path.join(test_data_dir, "recipes_full_content.csv")
    
    # Create minimal test data
    with open(agents_csv, 'w') as f:
        f.write("""name,slug,short_desc,long_desc,platform,pricing,creator,domain,use_case,model,rating,reviews_count,website,github,created_at,updated_at
ChatGPT,chatgpt,AI chatbot for conversations,Advanced language model for text generation,OpenAI,Free/Plus,OpenAI,General,Conversation,GPT-4,4.5,1000,https://chat.openai.com,,2023-01-01,2023-12-01
AutoGPT,autogpt,Autonomous AI agent,Self-prompting AI agent for task automation,GitHub,Free,Significant Gravitas,Automation,Task Automation,GPT-4,4.2,500,https://autogpt.net,https://github.com/Significant-Gravitas/AutoGPT,2023-03-01,2023-11-01""")
    
    with open(recipes_csv, 'w') as f:
        f.write("""name,slug,synopsis,description,agents_used,steps,outcomes,category,author,created_at
Content Generation,content-generation,Automate content creation,Use AI to generate blog posts and social media content,"ChatGPT, AutoGPT","1. Define content topic\n2. Generate outline\n3. Create content\n4. Review and edit",Increased content output by 300%,Content Marketing,John Doe,2023-06-01
Customer Support,customer-support,Automate customer inquiries,Handle common customer questions automatically,"ChatGPT, AutoGPT","1. Analyze customer query\n2. Generate response\n3. Escalate if needed",Reduced response time by 70%,Customer Service,Jane Smith,2023-07-01""")
    
    return {
        'agents_csv': agents_csv,
        'recipes_csv': recipes_csv
    }

@pytest.fixture
def mock_blog_files(test_data_dir):
    """Create mock blog files for testing."""
    blog_dir = os.path.join(test_data_dir, "blogs")
    os.makedirs(blog_dir, exist_ok=True)
    
    blog_files = [
        ("getting-started.md", """---
title: Getting Started with AI Agents
slug: getting-started
publish_date: 2023-01-15
category: Guides
tags: [beginner, tutorial, ai-agents]
meta_description: Learn how to get started with AI agents
featured_image: /images/getting-started.jpg
---

# Getting Started with AI Agents

This is a test blog post about getting started with AI agents.
"""),
        ("ai-automation.md", """---
title: AI Automation Guide
slug: ai-automation
publish_date: 2023-02-20
category: Tutorials
tags: [automation, workflow, productivity]
meta_description: Complete guide to AI automation
featured_image: /images/automation.jpg
---

# AI Automation Guide

This is a test blog post about AI automation.
""")
    ]
    
    for filename, content in blog_files:
        with open(os.path.join(blog_dir, filename), 'w') as f:
            f.write(content)
    
    return blog_dir

@pytest.fixture
def mock_user_data():
    """Mock user data for testing."""
    return {
        'test_user': {
            'email': 'test@example.com',
            'password': 'password123',
            'first_name': 'Test',
            'last_name': 'User'
        },
        'admin_user': {
            'email': 'admin@example.com',
            'password': 'admin123',
            'first_name': 'Admin',
            'last_name': 'User'
        }
    }

@pytest.fixture
def mock_google_credentials():
    """Mock Google service account credentials."""
    return {
        'type': 'service_account',
        'project_id': 'test-project',
        'private_key_id': 'test-key-id',
        'private_key': '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----\n',
        'client_email': 'test@test-project.iam.gserviceaccount.com',
        'client_id': 'test-client-id',
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
        'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/test%40test-project.iam.gserviceaccount.com'
    }

@pytest.fixture
def mock_google_apps_response():
    """Mock Google Apps API response."""
    return {
        'applications': [
            {
                'id': 'app1',
                'name': 'Gmail',
                'description': 'Email service',
                'status': 'ACTIVE',
                'type': 'GSUITE',
                'creationTime': '2023-01-01T00:00:00Z',
                'lastModifiedTime': '2023-12-01T00:00:00Z'
            },
            {
                'id': 'app2',
                'name': 'Google Drive',
                'description': 'File storage service',
                'status': 'ACTIVE',
                'type': 'GSUITE',
                'creationTime': '2023-01-01T00:00:00Z',
                'lastModifiedTime': '2023-12-01T00:00:00Z'
            }
        ]
    }

@pytest.fixture
def mock_rating_data():
    """Mock rating data for testing."""
    return {
        'agent_slug': 'chatgpt',
        'rating': 5,
        'review': 'Excellent AI agent for conversations!',
        'user_email': 'test@example.com'
    }

@pytest.fixture
def mock_demo_request_data():
    """Mock demo request data for testing."""
    return {
        'company_name': 'Test Company Inc.',
        'email': 'demo@testcompany.com',
        'team_size': '10-50',
        'ai_usage': 'We currently use AI for content generation and customer support automation.'
    }

@pytest.fixture
def mock_agent_data():
    """Mock agent data for testing."""
    return {
        'name': 'Test AI Agent',
        'description': 'A test AI agent for testing purposes',
        'platform': 'OpenAI',
        'pricing': 'Free',
        'creator': 'Test Creator',
        'domain': 'Testing',
        'use_case': 'Testing',
        'model': 'GPT-4',
        'website': 'https://test-agent.com',
        'github': 'https://github.com/test/test-agent'
    }

@pytest.fixture
def mock_search_results():
    """Mock search results for testing."""
    return {
        'agents': [
            {
                'name': 'ChatGPT',
                'slug': 'chatgpt',
                'short_desc': 'AI chatbot for conversations',
                'platform': 'OpenAI',
                'rating': 4.5
            },
            {
                'name': 'AutoGPT',
                'slug': 'autogpt',
                'short_desc': 'Autonomous AI agent',
                'platform': 'GitHub',
                'rating': 4.2
            }
        ],
        'recipes': [
            {
                'name': 'Content Generation',
                'slug': 'content-generation',
                'synopsis': 'Automate content creation'
            }
        ],
        'blog_posts': [
            {
                'title': 'Getting Started with AI Agents',
                'slug': 'getting-started',
                'meta_description': 'Learn how to get started with AI agents'
            }
        ]
    }

@pytest.fixture
def mock_filter_options():
    """Mock filter options for testing."""
    return {
        'domains': ['Marketing', 'Engineering', 'Product', 'Support'],
        'platforms': ['OpenAI', 'Anthropic', 'Google', 'GitHub'],
        'models': ['GPT-4', 'Claude', 'PaLM', 'GPT-3.5'],
        'creators': ['OpenAI', 'Anthropic', 'Google', 'Significant Gravitas'],
        'pricing': ['Free', 'Paid', 'Freemium', 'Enterprise']
    }

@pytest.fixture
def mock_blog_categories():
    """Mock blog categories for testing."""
    return ['Guides', 'Tutorials', 'News', 'Case Studies', 'Reviews']

@pytest.fixture
def mock_blog_tags():
    """Mock blog tags for testing."""
    return ['ai-agents', 'automation', 'productivity', 'tutorial', 'beginner', 'advanced']

@pytest.fixture(autouse=True)
def mock_external_services():
    """Mock external services to avoid real API calls during testing."""
    with patch('routes.pyrequests.get') as mock_get, \
         patch('routes.service_account.Credentials.from_service_account_info') as mock_creds:
        
        # Mock successful responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'applications': []}
        mock_creds.return_value = MagicMock(token='test_token', expired=False)
        
        yield {
            'mock_get': mock_get,
            'mock_creds': mock_creds
        }

@pytest.fixture
def test_client_with_session():
    """Test client with session data."""
    from app import create_app
    from models import db
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        client = app.test_client()
        
        # Set up session data
        with client.session_transaction() as sess:
            sess['session_token'] = 'test_session_token'
        
        yield client
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def authenticated_client(test_client_with_session, mock_external_services):
    """Test client with authenticated user."""
    mock_external_services['mock_auth'].return_value = {
        'success': True,
        'user': {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    }
    
    return test_client_with_session

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "ui: marks tests as UI tests"
    )

def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their names."""
    for item in items:
        # Mark tests based on their names
        if 'api' in item.name.lower():
            item.add_marker(pytest.mark.api)
        if 'ui' in item.name.lower() or 'page' in item.name.lower():
            item.add_marker(pytest.mark.ui)
        if 'integration' in item.name.lower():
            item.add_marker(pytest.mark.integration)
        if 'performance' in item.name.lower() or 'time' in item.name.lower():
            item.add_marker(pytest.mark.slow)
        else:
            item.add_marker(pytest.mark.unit) 