import pytest
from datetime import datetime
from models import db, User, Organization, ToolCatalog, UsageLog, ComplianceEvent
from werkzeug.security import generate_password_hash
import uuid

@pytest.fixture
def org():
    return Organization(
        id="org-1",
        name="Acme Corp",
        domain="acme.com",
        sso_provider="okta",
        sso_config={"issuer": "https://acme.okta.com"}
    )

@pytest.fixture
def community_user():
    return User(
        id=str(uuid.uuid4()),
        email='community@example.com',
        password_hash=generate_password_hash('password'),
        role='community',
        primary_role='community',
        roles=['community'],
        status='active'
    )

@pytest.fixture
def enterprise_user(org):
    return User(
        id=str(uuid.uuid4()),
        email='enterprise@example.com',
        password_hash=generate_password_hash('password'),
        organization_id=org.id,
        organization=org,
        role='employee',
        primary_role='employee',
        roles=['employee', 'manager'],
        department='Engineering',
        status='active'
    )

@pytest.fixture
def admin_user(org):
    return User(
        id=str(uuid.uuid4()),
        email='admin@example.com',
        password_hash=generate_password_hash('password'),
        organization_id=org.id,
        organization=org,
        role='admin',
        primary_role='admin',
        roles=['admin', 'employee'],
        status='active'
    )

def test_community_user_properties(community_user):
    assert community_user.is_community()
    assert not community_user.is_enterprise()
    assert not community_user.is_admin()
    assert community_user.has_role("community")
    assert community_user.status == "active"
    assert community_user.organization is None

def test_enterprise_user_properties(enterprise_user, org):
    assert not enterprise_user.is_community()
    assert enterprise_user.is_enterprise()
    assert not enterprise_user.is_admin()
    assert enterprise_user.has_role("employee")
    assert enterprise_user.has_role("manager")
    assert enterprise_user.organization == org
    assert enterprise_user.department == "Engineering"
    assert enterprise_user.team == "Platform"
    assert enterprise_user.status == "active"

def test_admin_user_properties(admin_user, org):
    assert not admin_user.is_community()
    assert admin_user.is_enterprise()
    assert admin_user.is_admin()
    assert admin_user.has_role("admin")
    assert admin_user.has_role("employee")
    assert admin_user.organization == org
    assert admin_user.status == "active"

def test_user_role_assignment():
    user = User(
        id="user-4",
        email="bob@acme.com",
        full_name="Bob Jones",
        primary_role="employee",
        roles=["employee", "security", "finance"]
    )
    assert user.has_role("employee")
    assert user.has_role("security")
    assert user.has_role("finance")
    assert not user.has_role("admin")

def test_user_status_and_timestamps():
    now = datetime.utcnow()
    user = User(
        id="user-5",
        email="tim@acme.com",
        full_name="Tim Lee",
        primary_role="employee",
        roles=["employee"],
        status="invited",
        created_at=now,
        updated_at=now,
        last_login=None
    )
    assert user.status == "invited"
    assert user.created_at == now
    assert user.updated_at == now
    assert user.last_login is None

def test_organization_fields(org):
    assert org.name == "Acme Corp"
    assert org.domain == "acme.com"
    assert org.sso_provider == "okta"
    assert org.sso_config["issuer"] == "https://acme.okta.com"

def test_tool_catalog_creation():
    tool = ToolCatalog(
        id="tool-1",
        name="ChatGPT",
        type="chatbot",
        vendor="OpenAI",
        description="Conversational AI agent",
        website="https://chat.openai.com",
        api_available=True,
        integration_method="browser_agent",
        extra={"category": "LLM"}
    )
    assert tool.name == "ChatGPT"
    assert tool.api_available is True
    assert tool.vendor == "OpenAI"
    assert tool.integration_method == "browser_agent"
    assert tool.extra["category"] == "LLM"

def test_usage_log_creation_and_relationships(org):
    user = User(
        id="user-6",
        email="eve@acme.com",
        full_name="Eve Adams",
        primary_role="employee",
        roles=["employee"],
        organization=org
    )
    tool = ToolCatalog(
        id="tool-2",
        name="Claude",
        type="chatbot",
        vendor="Anthropic",
        description="Anthropic's conversational AI",
        website="https://claude.ai",
        api_available=False,
        integration_method="browser_agent"
    )
    log = UsageLog(
        id="log-1",
        user=user,
        organization=org,
        tool=tool,
        tool_id=tool.id,
        tool_name=tool.name,
        action_type="prompt",
        timestamp=datetime(2024, 6, 1, 12, 0, 0),
        extra={"prompt": "Hello, Claude!"},
        source="browser",
        anonymized=False
    )
    assert log.user == user
    assert log.organization == org
    assert log.tool == tool
    assert log.tool_name == "Claude"
    assert log.action_type == "prompt"
    assert log.extra["prompt"] == "Hello, Claude!"
    assert log.source == "browser"
    assert not log.anonymized
    # Relationship reverse lookups
    assert log in user.usage_logs
    assert log in org.usage_logs
    assert log in tool.usage_logs

def test_compliance_event_creation_and_relationships(org):
    user = User(
        id="user-7",
        email="bob@acme.com",
        full_name="Bob Compliance",
        primary_role="employee",
        roles=["employee"],
        organization=org
    )
    tool = ToolCatalog(
        id="tool-3",
        name="Notion AI",
        type="productivity",
        vendor="Notion",
        description="AI features in Notion",
        website="https://notion.so",
        api_available=False,
        integration_method="browser_agent"
    )
    event = ComplianceEvent(
        id="event-1",
        user=user,
        organization=org,
        tool=tool,
        tool_id=tool.id,
        event_type="policy_violation",
        event_time=datetime(2024, 6, 2, 10, 0, 0),
        severity="critical",
        description="Sensitive data shared in Notion AI.",
        details={"policy": "No PII", "field": "SSN"},
        source="browser_agent",
        resolved=False
    )
    assert event.user == user
    assert event.organization == org
    assert event.tool == tool
    assert event.event_type == "policy_violation"
    assert event.severity == "critical"
    assert event.description.startswith("Sensitive data")
    assert event.details["policy"] == "No PII"
    assert event.source == "browser_agent"
    assert not event.resolved
    # Relationship reverse lookups
    assert event in user.compliance_events
    assert event in org.compliance_events
    assert event in tool.compliance_events 