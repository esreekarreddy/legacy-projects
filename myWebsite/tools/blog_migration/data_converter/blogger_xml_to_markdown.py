#!/usr/bin/env python3
"""
Blogger XML to Markdown Migration Tool

This script converts Blogger XML export files to Markdown files
and stores comments in a SQLite database for later integration.
"""

import os
import re
import sys
import sqlite3
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from html import unescape
import html2text

# Configuration
BLOGGER_NS = {'atom': 'http://www.w3.org/2005/Atom'}
CONTENT_DIR = '../content/blog/posts'
DB_PATH = 'comments.sqlite'

def setup_database():
    """Create SQLite database and tables for comments"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with open('schema.sql', 'r') as f:
        schema = f.read()
        cursor.executescript(schema)
    
    conn.commit()
    return conn

def slugify(title):
    """Convert title to slug for filename"""
    # Remove special chars, replace spaces with hyphens, convert to lowercase
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = re.sub(r'^-+|-+$', '', slug)
    return slug

def html_to_markdown(html_content):
    """Convert HTML content to Markdown"""
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_tables = False
    h.ignore_emphasis = False
    h.body_width = 0  # Don't wrap text
    
    # Add these settings for better line break handling
    h.wrap_links = False
    h.wrap_lists = False
    h.single_line_break = True  # Respect original line breaks
    h.br_style = '  '  # Add two spaces at end of line for Markdown line break
    
    return h.handle(html_content)

def extract_posts_and_comments(xml_path):
    """Parse Blogger XML and extract posts and comments"""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    posts = []
    comments = []
    
    # Process all entries
    for entry in root.findall('.//atom:entry', BLOGGER_NS):
        kind = None
        # Check if this entry is a post or comment
        for category in entry.findall('./atom:category', BLOGGER_NS):
            if category.get('scheme') == 'http://schemas.google.com/g/2005#kind':
                kind = category.get('term')
        
        # Process post entries
        if kind and 'post' in kind:
            post = {}
            post['id'] = entry.find('./atom:id', BLOGGER_NS).text
            
            # Get title
            title_elem = entry.find('./atom:title', BLOGGER_NS)
            post['title'] = title_elem.text if title_elem is not None and title_elem.text else 'Untitled'
            
            # Get publish date
            published = entry.find('./atom:published', BLOGGER_NS).text
            post['date'] = datetime.fromisoformat(published.replace('Z', '+00:00'))
            
            # Get content
            content = entry.find('./atom:content', BLOGGER_NS)
            post['content'] = content.text if content is not None and content.text else ''
            
            # Get author
            author = entry.find('./atom:author/atom:name', BLOGGER_NS)
            post['author'] = author.text if author is not None and author.text else 'Unknown'
            
            # Get URL (for slug)
            link = entry.find("./atom:link[@rel='alternate']", BLOGGER_NS)
            if link is not None:
                post['url'] = link.get('href')
                # Extract slug from URL
                post['slug'] = post['url'].split('/')[-1]
                if '.html' in post['slug']:
                    post['slug'] = post['slug'].split('.html')[0]
            else:
                post['slug'] = slugify(post['title'])
            
            posts.append(post)
        
        # Process comment entries
        elif kind and 'comment' in kind:
            comment = {}
            comment['id'] = entry.find('./atom:id', BLOGGER_NS).text
            
            # Get published date
            published = entry.find('./atom:published', BLOGGER_NS).text
            comment['date'] = datetime.fromisoformat(published.replace('Z', '+00:00'))
            
            # Get content
            content = entry.find('./atom:content', BLOGGER_NS)
            comment['content'] = content.text if content is not None and content.text else ''
            
            # Get author
            author = entry.find('./atom:author/atom:name', BLOGGER_NS)
            comment['author'] = author.text if author is not None and author.text else 'Anonymous'
            
            # Get post ID this comment belongs to
            reply_to = entry.find('./thr:in-reply-to', 
                                {'thr': 'http://purl.org/syndication/thread/1.0'})
            if reply_to is not None:
                comment['post_id'] = reply_to.get('ref')
                
            # Check if this is a reply to another comment
            # Look for parent comment reference - typically in the 'title' or might be in another tag
            title = entry.find('./atom:title', BLOGGER_NS)
            if title is not None and title.text is not None:
                # Try to extract parent info from title like "In reply to <name>"
                # Note: We'll need a second pass to actually link comments together
                comment['reply_title'] = title.text
                
            comments.append(comment)
    
    # Enhanced second pass - better detect parent-child relationships
    print("Analyzing comment relationships...")
    # First map comments by their IDs for easier lookup
    comments_by_id = {comment['id']: comment for comment in comments}
    
    # Look at the Blogger structure more carefully
    for comment in comments:
        # Skip comments that already have a parent set
        if 'parent_comment_id' in comment and comment['parent_comment_id']:
            continue
            
        # Check for 'in-reply-to' relationship in the title
        reply_title = comment.get('reply_title', '')
        if reply_title and reply_title.startswith('In reply to '):
            # Extract author name from the title (Blogger format: "In reply to Author")
            reply_to_author = reply_title[12:].strip()
            
            # Find most recent comment by this author before the current comment
            potential_parents = []
            for other_id, other in comments_by_id.items():
                if (other['author'].lower() == reply_to_author.lower() and 
                    other['date'] < comment['date'] and
                    other['post_id'] == comment['post_id'] and
                    other['id'] != comment['id']):
                    potential_parents.append(other)
            
            # If we found potential parents, use the most recent one
            if potential_parents:
                most_recent = max(potential_parents, key=lambda x: x['date'])
                comment['parent_comment_id'] = most_recent['id']
                print(f"Found parent for comment by {comment['author']}: replying to {most_recent['author']}")
    
    # Now continue with our existing parent detection for comments without a parent
    for comment in comments:
        if 'parent_comment_id' in comment and comment['parent_comment_id']:
            continue
            
        content = comment.get('content', '').lower()
        
        # Try to detect if this is a reply to another comment
        for other in comments:
            # Skip self-comparison
            if comment['id'] == other['id']:
                continue
                
            # Only consider comments on the same post
            if comment['post_id'] != other['post_id']:
                continue
                
            # Check if this comment is replying to the other comment
            other_author = other['author'].lower()
            
            # Expanded pattern matching
            patterns = [
                f"@{other_author}",
                f"reply to {other_author}",
                f"replying to {other_author}",
                f"in response to {other_author}",
                f"responding to {other_author}",
                f"hi {other_author}",
                f"hello {other_author}",
                f"hey {other_author}",
                f"dear {other_author}",
                f"{other_author}:",
                f"{other_author.split()[0]}," # First name with comma
            ]
            
            is_reply = False
            for pattern in patterns:
                if pattern in content:
                    # If the comment was made after the potential parent
                    if comment['date'] > other['date']:
                        is_reply = True
                        break
            
            if is_reply:
                comment['parent_comment_id'] = other['id']
                print(f"Detected relationship: Comment by {comment['author']} is replying to {other['author']}")
                break
    
    return posts, comments

def save_posts_as_markdown(posts, output_dir):
    """Save posts as Markdown files"""
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    for post in posts:
        # Create front matter
        front_matter = f"""---
title: {post['title']}
date: {post['date'].strftime('%Y-%m-%d')}
author: {post['author']}
summary: {post['title']}
post_id: {post['id']}
---

"""
        # Convert content from HTML to Markdown
        content = html_to_markdown(unescape(post['content']))
        
        # Combine front matter and content
        markdown_content = front_matter + content
        
        # Save to file
        file_path = os.path.join(output_dir, f"{post['slug']}.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✅ Saved post: {file_path}")

def save_comments_to_db(comments, posts, conn):
    """Save comments to SQLite database"""
    cursor = conn.cursor()
    
    # Create a mapping from post ID to slug for easier reference
    post_id_to_slug = {post['id']: post['slug'] for post in posts}
    
    # First pass: insert all comments without parent relationships
    comment_id_to_db_id = {}
    
    for comment in comments:
        # Skip comments without a post ID
        if 'post_id' not in comment:
            continue
        
        # Get the post slug this comment belongs to
        post_slug = post_id_to_slug.get(comment['post_id'])
        if not post_slug:
            continue
            
        # Insert comment into database
        cursor.execute('''
            INSERT INTO comments (
                comment_id, 
                post_id, 
                author_name, 
                content, 
                created_at, 
                status
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            comment['id'],
            post_slug,
            comment['author'],
            comment['content'],
            comment['date'].isoformat(),
            'approved'  # Assuming all existing comments are approved
        ))
        
        # Store the database ID of this comment
        comment_id_to_db_id[comment['id']] = cursor.lastrowid
    
    # Second pass: Update parent relationships with improved logging
    parent_relationships = 0
    for comment in comments:
        if comment.get('parent_comment_id') and comment['id'] in comment_id_to_db_id:
            # If we found a parent reference in the first pass
            if comment['parent_comment_id'] in comment_id_to_db_id:
                db_id = comment_id_to_db_id[comment['id']]
                parent_db_id = comment_id_to_db_id[comment['parent_comment_id']]
                
                cursor.execute('''
                    UPDATE comments SET parent_id = ? WHERE id = ?
                ''', (parent_db_id, db_id))
                parent_relationships += 1
    
    conn.commit()
    print(f"✅ Saved {len(comments)} comments to database with {parent_relationships} parent-child relationships")

def main():
    parser = argparse.ArgumentParser(description='Convert Blogger XML to Markdown files and SQLite comments')
    parser.add_argument('xml_file', help='Path to the Blogger XML export file')
    parser.add_argument('--output', default=CONTENT_DIR, help=f'Output directory for Markdown files (default: {CONTENT_DIR})')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.xml_file):
        print(f"Error: XML file not found: {args.xml_file}")
        return 1
    
    try:
        # Setup database
        print("Setting up comments database...")
        conn = setup_database()
        
        # Parse XML and extract posts/comments
        print(f"Parsing {args.xml_file}...")
        posts, comments = extract_posts_and_comments(args.xml_file)
        print(f"Found {len(posts)} posts and {len(comments)} comments")
        
        # Save posts as Markdown
        print(f"Saving posts to {args.output}...")
        save_posts_as_markdown(posts, args.output)
        
        # Save comments to database
        print("Saving comments to database...")
        save_comments_to_db(comments, posts, conn)
        
        print("\n✅ Migration complete!")
        print(f"  • {len(posts)} posts saved to {args.output}")
        print(f"  • {len(comments)} comments saved to {DB_PATH}")
        print("\nNext steps:")
        print("  1. Review the generated Markdown files")
        print("  2. Use the comments.sqlite database to integrate comments with your blog")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
