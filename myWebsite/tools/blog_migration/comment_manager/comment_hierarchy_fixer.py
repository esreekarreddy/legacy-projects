#!/usr/bin/env python3
"""
Comment Hierarchy Fixer

This script helps restructure existing comments to establish proper parent-child 
relationships that might have been missed during the initial migration.
"""

import os
import sqlite3
import argparse
from datetime import datetime

def connect_to_db(db_path):
    """Connect to SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_post_comments(conn, post_id):
    """Get all comments for a specific post."""
    cursor = conn.cursor()
    comments = cursor.execute(
        'SELECT * FROM comments WHERE post_id = ? ORDER BY created_at',
        [post_id]
    ).fetchall()
    return comments

def get_all_posts(conn):
    """Get list of all unique post_ids in the database."""
    cursor = conn.cursor()
    posts = cursor.execute('SELECT DISTINCT post_id FROM comments').fetchall()
    return [p['post_id'] for p in posts]

def analyze_comments(comments):
    """Analyze comments to suggest potential parent-child relationships."""
    suggestions = []
    
    # Sort comments by date (oldest first)
    sorted_comments = sorted(comments, key=lambda c: c['created_at'])
    
    for i, comment in enumerate(sorted_comments):
        # Skip if comment already has a parent assigned
        if comment['parent_id'] is not None:
            continue
            
        # Look for potential reply indicators in content
        content = comment['content'].lower()
        
        # For each previous comment, check if this might be a reply
        for j in range(i):
            potential_parent = sorted_comments[j]
            parent_author = potential_parent['author_name'].lower()
            
            # Skip if the potential parent already has this comment as a reply
            if potential_parent['id'] == comment['parent_id']:
                continue
                
            # Check for various reply patterns
            reply_indicators = [
                f"@{parent_author}",
                f"to {parent_author}:",
                f"@{parent_author.split()[0]}",  # First name only
                f"hi {parent_author}",
                f"hey {parent_author}",
                f"dear {parent_author}",
                f"{parent_author}:"
            ]
            
            is_potential_reply = False
            for indicator in reply_indicators:
                if indicator in content:
                    is_potential_reply = True
                    break
                    
            if is_potential_reply:
                time_diff = (datetime.fromisoformat(comment['created_at']) - 
                            datetime.fromisoformat(potential_parent['created_at'])).total_seconds()
                # Only suggest if the comment was made within 7 days of the potential parent
                if 0 <= time_diff <= 604800:  # 7 days in seconds
                    suggestions.append((comment['id'], potential_parent['id'], parent_author))
    
    return suggestions

def print_comment_thread(comments, post_id):
    """Print current comment thread structure."""
    print(f"\nCurrent comment thread for post '{post_id}':")
    print("=" * 50)
    
    # Create a dictionary of comments by ID for easy access
    comments_by_id = {c['id']: c for c in comments}
    
    # Create a dictionary to track which comments are replies
    is_reply = {c['id']: False for c in comments}
    for c in comments:
        if c['parent_id'] is not None:
            is_reply[c['parent_id']] = True
    
    # Print top-level comments and their replies
    for comment in comments:
        # Skip replies, we'll handle them when printing their parents
        if comment['parent_id'] is not None:
            continue
            
        # Print the comment
        print(f"ID: {comment['id']} - {comment['author_name']} ({comment['created_at'][:10]})")
        print(f"  {comment['content'][:100]}{'...' if len(comment['content']) > 100 else ''}")
        
        # Print any replies
        print_replies(comments, comment['id'], 1)
        print()
    
    print("=" * 50)

def print_replies(comments, parent_id, depth):
    """Recursively print replies to a comment."""
    for comment in comments:
        if comment['parent_id'] == parent_id:
            indent = "  " * depth
            print(f"{indent}↳ ID: {comment['id']} - {comment['author_name']} ({comment['created_at'][:10]})")
            print(f"{indent}  {comment['content'][:100]}{'...' if len(comment['content']) > 100 else ''}")
            print_replies(comments, comment['id'], depth + 1)

def set_parent(conn, comment_id, parent_id):
    """Set the parent of a comment."""
    cursor = conn.cursor()
    cursor.execute('UPDATE comments SET parent_id = ? WHERE id = ?', [parent_id, comment_id])
    conn.commit()
    print(f"Set comment {comment_id} as a reply to comment {parent_id}")

def interactive_mode(conn):
    """Interactive mode for fixing comment hierarchies."""
    posts = get_all_posts(conn)
    
    print(f"Found {len(posts)} posts with comments")
    for i, post_id in enumerate(posts):
        comments = get_post_comments(conn, post_id)
        print(f"\nPost {i+1}/{len(posts)}: '{post_id}' - {len(comments)} comments")
        
        suggestions = analyze_comments(comments)
        if suggestions:
            print(f"Found {len(suggestions)} potential parent-child relationships")
            
            # Print current thread structure
            print_comment_thread(comments, post_id)
            
            # Process suggestions
            for comment_id, parent_id, parent_author in suggestions:
                comment = next(c for c in comments if c['id'] == comment_id)
                response = input(f"\nComment {comment_id} by {comment['author_name']} might be a reply to comment {parent_id} by {parent_author}.\n"
                               f"Comment content: {comment['content'][:100]}{'...' if len(comment['content']) > 100 else ''}\n"
                               f"Set as reply? (y/n/s=skip post): ").lower()
                               
                if response == 'y':
                    set_parent(conn, comment_id, parent_id)
                elif response == 's':
                    break
            
            # Print updated thread structure
            comments = get_post_comments(conn, post_id)
            print_comment_thread(comments, post_id)
        else:
            print("No potential parent-child relationships found for this post.")
        
        # Ask if user wants to continue to next post
        if i < len(posts) - 1:
            response = input("\nContinue to next post? (y/n): ").lower()
            if response != 'y':
                break

def manual_mode(conn):
    """Manual mode for setting parent-child relationships directly."""
    while True:
        post_id = input("\nEnter post_id (or 'list' to see all posts, 'quit' to exit): ")
        
        if post_id.lower() == 'quit':
            break
            
        if post_id.lower() == 'list':
            posts = get_all_posts(conn)
            print("\nAvailable posts:")
            for i, p in enumerate(posts):
                print(f"{i+1}. {p}")
            continue
            
        comments = get_post_comments(conn, post_id)
        if not comments:
            print(f"No comments found for post '{post_id}'")
            continue
            
        print_comment_thread(comments, post_id)
        
        while True:
            command = input("\nEnter 'set COMMENT_ID PARENT_ID' to set parent, or 'done' to finish with this post: ")
            
            if command.lower() == 'done':
                break
                
            parts = command.split()
            if len(parts) == 3 and parts[0].lower() == 'set':
                try:
                    comment_id = int(parts[1])
                    parent_id = int(parts[2])
                    
                    # Verify both IDs exist
                    comment = next((c for c in comments if c['id'] == comment_id), None)
                    parent = next((c for c in comments if c['id'] == parent_id), None)
                    
                    if not comment:
                        print(f"Comment ID {comment_id} not found")
                        continue
                        
                    if not parent:
                        print(f"Parent ID {parent_id} not found")
                        continue
                        
                    # Prevent circular references
                    if comment_id == parent_id:
                        print("Cannot set a comment as its own parent")
                        continue
                        
                    # Set the parent
                    set_parent(conn, comment_id, parent_id)
                    
                    # Refresh comments
                    comments = get_post_comments(conn, post_id)
                    print_comment_thread(comments, post_id)
                except ValueError:
                    print("Invalid command format. Use 'set COMMENT_ID PARENT_ID'")
            else:
                print("Invalid command. Use 'set COMMENT_ID PARENT_ID' or 'done'")

def reset_parent(conn, comment_id):
    """Reset a comment's parent to NULL."""
    cursor = conn.cursor()
    cursor.execute('UPDATE comments SET parent_id = NULL WHERE id = ?', [comment_id])
    conn.commit()
    print(f"Reset parent for comment {comment_id}")

def main():
    parser = argparse.ArgumentParser(description='Fix comment hierarchy structure')
    parser.add_argument('--db', default='../comments.sqlite',
                        help='Path to comments SQLite database')
    parser.add_argument('--mode', default='interactive',
                        choices=['interactive', 'manual', 'auto'],
                        help='Mode to run in (interactive, manual, auto)')
    parser.add_argument('--reset', type=int, help='Reset parent for a specific comment ID')
    
    args = parser.parse_args()
    
    conn = connect_to_db(args.db)
    
    if args.reset:
        reset_parent(conn, args.reset)
        return
    
    if args.mode == 'interactive':
        interactive_mode(conn)
    elif args.mode == 'manual':
        manual_mode(conn)
    elif args.mode == 'auto':
        posts = get_all_posts(conn)
        for post_id in posts:
            comments = get_post_comments(conn, post_id)
            suggestions = analyze_comments(comments)
            if suggestions:
                print(f"Post '{post_id}': Found {len(suggestions)} potential parent-child relationships")
                for comment_id, parent_id, _ in suggestions:
                    set_parent(conn, comment_id, parent_id)
            else:
                print(f"Post '{post_id}': No parent-child relationships found")
    
    conn.close()

if __name__ == "__main__":
    main()
