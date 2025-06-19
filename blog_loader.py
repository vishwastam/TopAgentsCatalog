"""
Blog data loader for Top Agents website
Handles markdown files and converts them to blog posts with proper metadata
"""

import os
import re
import frontmatter
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from urllib.parse import quote


@dataclass
class BlogPost:
    """Model class for representing a blog post"""
    title: str
    slug: str
    content: str
    excerpt: str
    author: str
    publish_date: datetime
    tags: List[str]
    category: str
    featured_image: Optional[str] = None
    meta_description: Optional[str] = None
    reading_time: Optional[int] = None
    
    def __post_init__(self):
        """Process blog post data after initialization"""
        # Generate excerpt if not provided
        if not self.excerpt:
            # Remove markdown formatting and get first 200 characters
            clean_content = re.sub(r'[#*`\[\]]', '', self.content)
            self.excerpt = clean_content[:200].strip() + '...' if len(clean_content) > 200 else clean_content
        
        # Calculate reading time if not provided
        if not self.reading_time:
            word_count = len(self.content.split())
            self.reading_time = max(1, word_count // 200)  # Average reading speed
        
        # Generate meta description if not provided
        if not self.meta_description:
            self.meta_description = self.excerpt[:160] + '...' if len(self.excerpt) > 160 else self.excerpt
    
    def get_json_ld(self) -> Dict[str, Any]:
        """Generate JSON-LD structured data for SEO"""
        base_url = os.environ.get('BASE_URL', 'https://top-agents.us')
        
        return {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": self.title,
            "description": self.meta_description,
            "author": {
                "@type": "Person",
                "name": self.author
            },
            "publisher": {
                "@type": "Organization",
                "name": "Top Agents",
                "url": base_url,
                "logo": {
                    "@type": "ImageObject",
                    "url": f"{base_url}/static/images/top-agents-logo.svg"
                }
            },
            "datePublished": self.publish_date.isoformat(),
            "dateModified": self.publish_date.isoformat(),
            "url": f"{base_url}/blog/{self.slug}",
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": f"{base_url}/blog/{self.slug}"
            },
            "image": self.featured_image if self.featured_image else f"{base_url}/static/images/blog-default.jpg",
            "articleSection": self.category,
            "keywords": ", ".join(self.tags),
            "wordCount": len(self.content.split()),
            "timeRequired": f"PT{self.reading_time}M"
        }


class BlogLoader:
    """Class to handle loading and processing blog posts from markdown files"""
    
    def __init__(self, blogs_dir: str = "blogs"):
        self.blogs_dir = blogs_dir
        self.posts = []
        self._load_posts()
    
    def _create_slug(self, title: str) -> str:
        """Create a URL-safe slug from blog title"""
        # Remove special characters and convert to lowercase
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        # Replace spaces and multiple hyphens with single hyphen
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')
    
    def _load_posts(self):
        """Load all blog posts from markdown files"""
        try:
            if not os.path.exists(self.blogs_dir):
                logging.warning(f"Blogs directory not found: {self.blogs_dir}")
                return
            
            # Get all .md files in the blogs directory
            md_files = [f for f in os.listdir(self.blogs_dir) if f.endswith('.md')]
            logging.info(f"Found {len(md_files)} blog posts in {self.blogs_dir}")
            
            for filename in md_files:
                try:
                    file_path = os.path.join(self.blogs_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse frontmatter if present
                    if content.startswith('---'):
                        post = frontmatter.loads(content)
                        metadata = post.metadata
                        content = post.content
                    else:
                        metadata = {}
                    
                    # Extract title from filename if not in metadata
                    title = metadata.get('title', filename.replace('.md', '').replace('-', ' ').title())
                    
                    # Create slug
                    slug = metadata.get('slug', self._create_slug(title))
                    
                    # Parse date
                    date_str = metadata.get('date', metadata.get('publish_date', '2024-01-01'))
                    if isinstance(date_str, str):
                        try:
                            publish_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        except ValueError:
                            publish_date = datetime(2024, 1, 1)
                    else:
                        publish_date = date_str
                    
                    # Create blog post
                    blog_post = BlogPost(
                        title=title,
                        slug=slug,
                        content=content,
                        excerpt=metadata.get('excerpt', ''),
                        author=metadata.get('author', 'Top Agents Team'),
                        publish_date=publish_date,
                        tags=metadata.get('tags', []),
                        category=metadata.get('category', 'General'),
                        featured_image=metadata.get('featured_image'),
                        meta_description=metadata.get('meta_description'),
                        reading_time=metadata.get('reading_time')
                    )
                    
                    self.posts.append(blog_post)
                    
                except Exception as e:
                    logging.error(f"Error processing blog file {filename}: {e}")
                    continue
            
            # Sort posts by publish date (newest first)
            self.posts.sort(key=lambda x: x.publish_date, reverse=True)
            logging.info(f"Successfully loaded {len(self.posts)} blog posts")
            
        except Exception as e:
            logging.error(f"Error loading blog posts: {e}")
    
    def get_all_posts(self) -> List[BlogPost]:
        """Get all blog posts"""
        return self.posts
    
    def get_published_posts(self) -> List[BlogPost]:
        """Get only published blog posts (not future dated)"""
        now = datetime.now()
        return [post for post in self.posts if post.publish_date <= now]
    
    def get_post_by_slug(self, slug: str) -> Optional[BlogPost]:
        """Get a specific blog post by its slug"""
        for post in self.posts:
            if post.slug == slug:
                return post
        return None
    
    def get_posts_by_category(self, category: str) -> List[BlogPost]:
        """Get all posts in a specific category"""
        return [post for post in self.posts if post.category.lower() == category.lower()]
    
    def get_posts_by_tag(self, tag: str) -> List[BlogPost]:
        """Get all posts with a specific tag"""
        return [post for post in self.posts if tag.lower() in [t.lower() for t in post.tags]]
    
    def get_recent_posts(self, limit: int = 5) -> List[BlogPost]:
        """Get the most recent blog posts"""
        return self.get_published_posts()[:limit]
    
    def get_featured_posts(self, limit: int = 3) -> List[BlogPost]:
        """Get featured blog posts (you can add a 'featured' field to markdown frontmatter)"""
        # For now, return recent posts. You can enhance this by adding a 'featured' field
        return self.get_recent_posts(limit)
    
    def get_categories(self) -> List[str]:
        """Get all unique categories"""
        categories = set()
        for post in self.posts:
            categories.add(post.category)
        return sorted(list(categories))
    
    def get_tags(self) -> List[str]:
        """Get all unique tags"""
        tags = set()
        for post in self.posts:
            tags.update(post.tags)
        return sorted(list(tags))


# Global instance for use in routes
blog_loader = BlogLoader() 