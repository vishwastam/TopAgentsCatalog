# Cursor Analytics Dashboard: Features & Technical Plan

## Overview
This document outlines the features, user stories, and technical implementation plan for a comprehensive analytics dashboard leveraging the Cursor Admin API. The dashboard is designed to provide actionable insights into team usage, AI adoption, spending, and more, with robust backend and frontend architecture.

---

## Feature List

### 1. Team Overview
- List all teams, members, and roles
- Show team creation date, last activity, and status

### 2. Usage Trends
- Daily/weekly/monthly active users
- Query and completion volume over time
- Top users by activity
- Heatmaps of usage by hour/day

### 3. AI Adoption Metrics
- Number of AI agents used per team/user
- Most popular agents and models
- New agent adoption trends

### 4. Spending & Billing
- Usage-based cost breakdown (by team, user, agent)
- Monthly/quarterly/yearly spend trends
- Alerts for budget thresholds

### 5. Deep Analytics
- Query success/failure rates
- Average response time per agent/model
- Error and exception tracking
- Custom event tracking (e.g., feature usage)

### 6. Custom Insights & Reporting
- Downloadable CSV/Excel reports
- Customizable dashboards (widgets, filters)
- Scheduled email reports

### 7. Export & Integration
- API endpoints for data export
- Webhooks for real-time events
- Integration with Slack, email, or other tools

### 8. AI-Generated Code Metrics
- Track lines of code suggested, added, or deleted by AI chat features
- Visualize accepted vs. rejected AI code suggestions
- Show per-user and aggregate AI code contribution

### 9. Feature Usage Metrics
- Monitor usage of key features: chat applies, accepts, rejects, tabs shown, tabs accepted
- Display trends and breakdowns by user, team, and time period
- Identify most/least used features for adoption analysis

### 10. Request Type Metrics
- Report on edit, ask, agent, and command palette (Cmd+K) requests
- Visualize request volumes and types over time
- Correlate request types with user activity and outcomes

---

## Metrics Details & Visualization

The dashboard will include dedicated sections and visualizations for the following metrics, as defined in the Cursor Analytics documentation ([source](https://docs.cursor.com/account/teams/analytics)):

### AI-Generated Code Metrics
- **Chat Suggested Lines Added/Deleted**: Total lines suggested by AI chat for addition/deletion
- **Chat Accepted Lines Added/Deleted**: AI-suggested lines actually accepted by users

### Feature Usage Metrics
- **Chat Total Applies**: Times AI-generated changes were applied
- **Chat Total Accepts/Rejects**: Times AI suggestions were accepted or rejected
- **Chat Tabs Shown/Accepted**: Tabs shown and accepted by users

### Request Type Metrics
- **Edit Requests**: Inline composer/edit feature usage
- **Ask Requests**: Chat questions to AI
- **Agent Requests**: Specialized AI agent requests
- **Cmd+K Usages**: Command palette usage

#### Visualization & Export
- Time series charts for each metric (daily/weekly/monthly)
- Per-user, per-team, and aggregate breakdowns
- Downloadable CSV/Excel reports with all metric headers as described in the analytics docs
- Filters for date range, user, team, and feature

---

## User Stories

- **As a superadmin**, I want to see a high-level overview of all teams and their activity so I can monitor adoption.
- **As a team lead**, I want to track my team’s usage and spending to optimize our AI workflows.
- **As a data analyst**, I want to export detailed usage data for custom analysis.
- **As a finance admin**, I want to receive alerts when spending exceeds a threshold.

---

## Technical Plan

### Backend
- **API Integration:**
  - Use the Cursor Admin API for all analytics data (team, user, agent, usage, billing, etc.)
  - Implement caching for expensive/slow queries
  - Use background jobs (e.g., Celery) for scheduled reports and heavy data processing
- **Endpoints:**
  - `/dashboard/overview` – Team/user/agent summary
  - `/dashboard/usage` – Usage trends and breakdowns
  - `/dashboard/billing` – Cost and spend analytics
  - `/dashboard/errors` – Error and exception logs
  - `/dashboard/export` – Data export endpoints
- **Security:**
  - Require superadmin or team admin authentication for access
  - Rate-limit API calls to prevent abuse
  - Sanitize and validate all inputs/filters

### Frontend
- **Framework:**
  - Use existing Flask/Jinja2 templates or React (if SPA)
  - Responsive, modern UI with charts (e.g., Chart.js, Plotly)
- **Pages/Views:**
  - Overview dashboard (key metrics, quick links)
  - Usage analytics (charts, filters, tables)
  - Billing/spending (trend lines, breakdowns)
  - Error logs (searchable, filterable)
  - Custom reports (download/export)
- **Interactivity:**
  - AJAX for dynamic data loading
  - Filters for date range, team, user, agent, etc.
  - Export buttons for CSV/Excel

### Integration Points
- **Cursor Admin API:**
  - Authentication (API key or OAuth)
  - Endpoints for teams, users, agents, usage, billing, errors
- **Internal DB (optional):**
  - Cache or store snapshots for performance
  - Store custom events or annotations

### Security Considerations
- Enforce RBAC (role-based access control)
- Secure API keys/secrets in environment variables
- Use HTTPS for all API and dashboard traffic
- Audit logs for dashboard access and data exports

---

## Next Steps
1. **API Schema Review:**
   - Review Cursor Admin API docs for all required endpoints and data fields
2. **Wireframe UI:**
   - Design dashboard layout and key views
3. **Backend Prototyping:**
   - Implement API integration and caching layer
4. **Frontend Prototyping:**
   - Build initial dashboard with static/mock data
5. **Iterative Development:**
   - Add features incrementally, test with real data
6. **Testing & QA:**
   - Unit, integration, and security tests
7. **Documentation:**
   - Update README and onboarding docs

---

## Contributors & Onboarding
- New contributors should review this document, the README, and the Cursor Admin API docs.
- For questions, contact the project maintainer or open an issue. 