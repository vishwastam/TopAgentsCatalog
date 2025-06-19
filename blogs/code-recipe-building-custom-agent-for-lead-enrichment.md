---
title: "Code Recipe: Building a Custom Agent for Lead Enrichment"
slug: "code-recipe-building-custom-agent-for-lead-enrichment"
date: "2025-06-19"
author: "Top Agents Team"
category: "Sales"
tags: ["Lead Enrichment", "AI Agents", "Sales Automation", "Coding"]
excerpt: "A hands-on code recipe to build an AI agent that enriches leads by pulling data from public APIs and CRMs."
meta_description: "Learn how to code an AI agent for automated lead enrichment, integrating external data sources and your CRM."
featured_image: https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800
reading_time: 12
---

# Code Recipe: Building a Custom Agent for Lead Enrichment

Accurate lead data is the lifeblood of any sales team. Manually researching prospects across LinkedIn, company websites, and databases like Clearbit or ZoomInfo consumes hours per week. With a custom AI agent, you can automate lead enrichment—fetching company details, social profiles, and firmographics—directly into your CRM. This recipe provides step-by-step code examples using Python, FastAPI, and OpenAI's API to build an agent that transforms a name and domain into a rich lead profile.

## Prerequisites

- Python 3.9+  
- An OpenAI API key  
- Access to a lead data API (e.g., Clearbit, FullContact)  
- CRM API credentials (e.g., Salesforce, HubSpot)  
- Optional: Redis for caching  

## 1. Setup and Dependencies

Install required packages:

```bash
pip install fastapi uvicorn openai requests redis
```

## 2. Define the Agent Interface

Create a `main.py` with the following content:

```python
from fastapi import FastAPI
import openai
import requests

app = FastAPI()
openai.api_key = "YOUR_OPENAI_KEY"

def get_company(domain: str):
    res = requests.get(
        f"https://company.clearbit.com/v2/companies/find?domain={domain}",
        auth=("YOUR_CLEARBIT_KEY", "")
    )
    return res.json()

@app.post("/enrich")
async def enrich_lead(name: str, domain: str):
    company = get_company(domain)

    prompt = f"""
Lead Name: {name}
Company: {company.get('name')}
Domain: {domain}
Industry: {company.get('category', {}).get('industry')}
Description: {company.get('description')}

Generate a lead profile summary with recommended next steps for outreach.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    summary = response.choices[0].message.content

    return {
        "name": name,
        "domain": domain,
        "company": company,
        "profile_summary": summary
    }
```

## 3. Caching for Efficiency

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_company(domain: str):
    cached = redis_client.get(domain)
    if cached:
        return json.loads(cached)
    res = requests.get(
        f"https://company.clearbit.com/v2/companies/find?domain={domain}",
        auth=("YOUR_CLEARBIT_KEY", "")
    ).json()
    redis_client.set(domain, json.dumps(res), ex=86400)
    return res
```

## 4. Integrating with CRM

```python
import hubspot
from hubspot.crm.contacts import SimplePublicObjectInput

hubspot_client = hubspot.Client.create(api_key="YOUR_HUBSPOT_KEY")

def create_or_update_contact(enriched):
    properties = {
        "email": enriched["domain"],
        "firstname": enriched["name"].split()[0],
        "company": enriched["company"].get("name"),
        "description": enriched["profile_summary"]
    }
    contact = SimplePublicObjectInput(properties=properties)
    hubspot_client.crm.contacts.basic_api.create(contact)
```

## 5. Running and Testing

```bash
uvicorn main:app --reload
```

```bash
curl -X POST "http://localhost:8000/enrich" -H "Content-Type: application/json" \
-d '{"name": "Jane Doe", "domain": "example.com"}'
```

## Real-World Impact

**XYZ Solutions** integrated this agent into their sales stack, enriching 500 leads daily. They observed a **20% uplift** in meeting conversions thanks to personalized outreach from AI-generated profiles.

## Best Practices

1. **Error Handling:** Gracefully handle 404s from Clearbit and fallback appropriately.  
2. **Rate Limits:** Monitor and respect API rate limits; implement exponential backoff.  
3. **Prompt Refinement:** Tweak GPT prompts to match your brand voice.  
4. **Privacy Compliance:** Redact PII before sending data to external APIs.

---

By following this code recipe, sales teams can automate lead enrichment at scale—ensuring every prospect record is complete and personalized, driving more effective outreach and higher conversion rates.
