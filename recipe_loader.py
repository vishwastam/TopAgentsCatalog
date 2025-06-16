"""
Recipe data loader for AI Agent Recipes
"""

import pandas as pd
import os
from typing import List, Dict, Any
from dataclasses import dataclass
import logging


@dataclass
class Recipe:
    """Model class for representing an AI Agent Recipe"""
    name: str
    synopsis: str
    detailed_synopsis: str
    target_audience: str
    why_it_works: str
    source_links: str
    slug: str = ""

    def __post_init__(self):
        """Clean and process recipe data after initialization"""
        self.name = self.name.strip() if self.name else ""
        self.synopsis = self.synopsis.strip() if self.synopsis else ""
        self.target_audience = self.target_audience.strip() if self.target_audience else ""
        self.why_it_works = self.why_it_works.strip() if self.why_it_works else ""
        self.source_links = self.source_links.strip() if self.source_links else ""
        
        # Generate slug if not provided
        if not self.slug:
            self.slug = self._create_slug(self.name)
    
    def _create_slug(self, name: str) -> str:
        """Create a URL-safe slug from recipe name"""
        import re
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def get_json_ld(self) -> Dict[str, Any]:
        """Generate JSON-LD structured data for SEO"""
        from flask import url_for
        
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": self.name,
            "description": self.synopsis,
            "articleBody": f"{self.synopsis} {self.why_it_works}",
            "author": {
                "@type": "Organization",
                "name": "Top Agents"
            },
            "publisher": {
                "@type": "Organization",
                "name": "Top Agents",
                "url": "https://topagents.com"
            },
            "datePublished": "2025-06-13",
            "dateModified": "2025-06-13",
            "url": url_for('recipe_detail', slug=self.slug, _external=True),
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": url_for('recipe_detail', slug=self.slug, _external=True)
            },
            "about": {
                "@type": "Thing",
                "name": "AI Agent Recipe",
                "description": self.synopsis
            },
            "audience": {
                "@type": "Audience",
                "name": self.target_audience
            },
            "keywords": f"AI agent, {self.target_audience.lower()}, automation, recipe"
        }


class RecipeLoader:
    """Class to handle loading and processing recipe data from CSV"""
    
    def __init__(self, csv_path: str = "recipes_full_content.csv"):
        self.csv_path = csv_path
        self.recipes = []
        self._load_data()
    
    def _load_data(self):
        """Load recipe data from CSV file"""
        try:
            if not os.path.exists(self.csv_path):
                logging.error(f"Recipe CSV file not found: {self.csv_path}")
                return
            
            df = pd.read_csv(self.csv_path)
            logging.info(f"Loading recipes from {self.csv_path}")
            
            for _, row in df.iterrows():
                try:
                    detailed_synopsis = str(row.get('Detailed Synopsis', ''))
                    # Create a shorter synopsis from the first sentence of detailed synopsis
                    short_synopsis = detailed_synopsis.split('.')[0] + '.' if detailed_synopsis else ''
                    if len(short_synopsis) > 200:
                        short_synopsis = short_synopsis[:200] + '...'
                    
                    recipe = Recipe(
                        name=str(row.get('Recipe Name', '')),
                        synopsis=short_synopsis,
                        detailed_synopsis=detailed_synopsis,
                        target_audience=str(row.get('Target Audience', '')),
                        why_it_works=str(row.get('Why It Works', '')),
                        source_links=str(row.get('Source Link(s)', ''))
                    )
                    self.recipes.append(recipe)
                except Exception as e:
                    logging.error(f"Error processing recipe row: {e}")
                    continue
            
            logging.info(f"Loaded {len(self.recipes)} recipes")
            
        except Exception as e:
            logging.error(f"Error loading recipe data: {e}")
    
    def get_all_recipes(self) -> List[Recipe]:
        """Get all loaded recipes"""
        return self.recipes
    
    def get_top_recipes(self, limit: int = 6) -> List[Recipe]:
        """Get random selection of recipes for homepage display"""
        import random
        if len(self.recipes) >= limit:
            return random.sample(self.recipes, limit)
        return self.recipes[:limit]
    
    def get_recipe_by_slug(self, slug: str):
        """Get a specific recipe by its slug"""
        for recipe in self.recipes:
            if recipe.slug == slug:
                return recipe
        return None


# Global instance for use in routes
recipe_loader = RecipeLoader()