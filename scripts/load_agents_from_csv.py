import csv
import os
import sys
from slugify import slugify

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from models import db, AIAgent
from app import create_app

app = create_app()

CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'combined_ai_agents_directory.csv')

REQUIRED_FIELDS = [
    'name', 'domains', 'use_cases', 'short_desc', 'long_desc', 'creator', 'url', 'platform', 'pricing'
]

# Helper to generate slug

def generate_slug(name):
    import re
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

with app.app_context():
    with open(CSV_PATH, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        for row in reader:
            # Skip rows with missing required fields
            if not all(row.get(f, '').strip() for f in REQUIRED_FIELDS):
                continue
            # Check if agent already exists by name or slug
            name = row['name'].strip()
            slug = generate_slug(name)
            if AIAgent.query.filter((AIAgent.name == name) | (AIAgent.slug == slug)).first():
                continue
            agent = AIAgent(
                name=name,
                slug=slug,
                short_desc=row['short_desc'].strip(),
                long_desc=row['long_desc'].strip(),
                creator=row['creator'].strip(),
                url=row['url'].strip(),
                platform=row['platform'].strip(),
                pricing=row['pricing'].strip(),
                domains=row['domains'].strip(),
                use_cases=row['use_cases'].strip(),
                underlying_model=row.get('underlying_model', '').strip(),
                deployment=row.get('deployment', '').strip(),
                legitimacy=row.get('legitimacy', '').strip()
            )
            db.session.add(agent)
            count += 1
        db.session.commit()
        print(f"Loaded {count} agents from CSV into the database.") 