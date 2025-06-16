from dataclasses import dataclass
from typing import List, Dict, Any
import re

@dataclass
class Agent:
    """Model class for representing an AI Agent"""
    name: str
    domains: str
    use_cases: str
    short_desc: str
    long_desc: str
    creator: str
    url: str
    platform: str
    pricing: str
    underlying_model: str
    deployment: str
    legitimacy: str
    what_users_think: str = ""
    
    def __post_init__(self):
        """Clean and process agent data after initialization"""
        # Create a URL-safe slug for the agent
        self.slug = self._create_slug(self.name)
        
        # Initialize rating properties
        self.average_rating = 0.0
        self.review_count = 0
        
        # Parse domains into a list
        self.domain_list = [d.strip() for d in self.domains.split(';') if d.strip()]
        
        # Parse use cases into a list
        self.use_case_list = [u.strip() for u in self.use_cases.split(';') if u.strip()]
        
        # Parse platforms into a list
        self.platform_list = [p.strip() for p in self.platform.split(';') if p.strip()]
        
        # Clean pricing information
        self.pricing_clean = self._clean_pricing(self.pricing)
        
        # Extract primary use case for filtering
        self.primary_use_case = self.use_case_list[0] if self.use_case_list else "General"
        
        # Extract primary domain
        self.primary_domain = self.domain_list[0] if self.domain_list else "General AI"
        
        # Ensure URL has proper protocol
        self.url = self._clean_url(self.url)
    
    def _create_slug(self, name: str) -> str:
        """Create a URL-safe slug from agent name"""
        # Remove special characters and convert to lowercase
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        # Replace spaces and multiple hyphens with single hyphen
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def _clean_pricing(self, pricing: str) -> str:
        """Clean and standardize pricing information"""
        pricing = pricing.strip()
        if not pricing or pricing.lower() in ['free', '']:
            return 'Free'
        elif 'freemium' in pricing.lower():
            return 'Freemium'
        elif any(word in pricing.lower() for word in ['paid', '$', 'subscription', 'plan']):
            return 'Paid'
        else:
            return pricing
    
    def _clean_url(self, url: str) -> str:
        """Clean and validate URL, ensuring it has proper protocol"""
        if not url or url.lower() in ['nan', 'none', 'null', '']:
            return ""
        
        url = url.strip()
        
        # If URL already has a protocol, return it
        if url.startswith(('http://', 'https://')):
            return url
        
        # If URL looks like a relative path, return it as is
        if url.startswith('/'):
            return url
        
        # For domain names without protocol, add https://
        if '.' in url and not url.startswith(('ftp://', 'file://')):
            return f"https://{url}"
        
        return url
    
    def get_json_ld(self) -> Dict[str, Any]:
        """Generate comprehensive JSON-LD structured data for SEO and semantic understanding"""
        # Base SoftwareApplication schema
        json_ld = {
            "@context": [
                "https://schema.org",
                {
                    "ai": "https://schema.org/",
                    "agent": "https://schema.org/SoftwareApplication"
                }
            ],
            "@type": ["SoftwareApplication", "WebApplication"],
            "@id": f"https://topagents.com/agents/{self.slug}",
            "name": self.name,
            "alternateName": f"{self.name} AI Agent",
            "description": self.short_desc,
            "abstract": self.long_desc if self.long_desc and self.long_desc != 'nan' else self.short_desc,
            "applicationCategory": ["AI Agent", "Artificial Intelligence", self.primary_domain],
            "applicationSubCategory": self.primary_use_case,
            "operatingSystem": ["Web", "Cloud", "API"] + (self.platform_list if hasattr(self, 'platform_list') else []),
            "url": self.url,
            "sameAs": [self.url] if self.url else [],
            "identifier": {
                "@type": "PropertyValue",
                "name": "slug",
                "value": self.slug
            },
            "creator": {
                "@type": "Organization",
                "name": self.creator,
                "url": self.url if self.creator.lower() in self.url.lower() else None
            },
            "author": {
                "@type": "Organization", 
                "name": self.creator
            },
            "publisher": {
                "@type": "Organization",
                "name": "Top Agents",
                "url": "https://topagents.com"
            },
            "offers": {
                "@type": "Offer",
                "price": "0" if self.pricing_clean == "Free" else None,
                "priceCurrency": "USD",
                "priceSpecification": {
                    "@type": "PriceSpecification",
                    "price": "0" if self.pricing_clean == "Free" else None,
                    "priceCurrency": "USD"
                },
                "availability": "https://schema.org/InStock",
                "description": self.pricing_clean
            },
            "keywords": [self.primary_domain, self.primary_use_case] + self.domain_list + self.use_case_list,
            "about": [
                {
                    "@type": "Thing",
                    "name": domain
                } for domain in self.domain_list
            ],
            "usageInfo": self.use_case_list,
            "featureList": self.use_case_list,
            "datePublished": "2024-01-01",
            "dateModified": "2025-01-01",
            "softwareVersion": "Latest",
            "isAccessibleForFree": self.pricing_clean == "Free",
            "softwareRequirements": "Internet Connection",
            "memoryRequirements": "Minimal",
            "processorRequirements": "Any",
            "storageRequirements": "Cloud-based",
            "screenshot": f"https://topagents.com/static/images/agents/{self.slug}-preview.png",
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "4.5",
                "bestRating": "5",
                "worstRating": "1",
                "ratingCount": "100"
            },
            "potentialAction": [
                {
                    "@type": "UseAction",
                    "name": f"Use {self.name}",
                    "target": self.url
                },
                {
                    "@type": "ViewAction", 
                    "name": f"View {self.name} Details",
                    "target": f"https://topagents.com/agents/{self.slug}"
                }
            ]
        }
        
        # Add underlying model information if available
        if hasattr(self, 'underlying_model') and self.underlying_model and self.underlying_model != 'nan':
            json_ld["softwareVersion"] = self.underlying_model
            json_ld["runtimePlatform"] = self.underlying_model
        
        # Add deployment information
        if hasattr(self, 'deployment') and self.deployment and self.deployment != 'nan':
            json_ld["deploymentMode"] = self.deployment
        
        return json_ld
