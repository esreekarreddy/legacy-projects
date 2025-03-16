#!/usr/bin/env python3
"""
Manual Comment Hierarchy Manager

This script helps you visualize all comments for each post and manually set parent-child relationships.
"""

import os
import sqlite3
import sys
from datetime import datetime
import textwrap

def connect_to_db(db_path):
    """Connect to SQLite database."""
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        sys.exit(1)
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_posts(conn):
    """Get all posts that have comments."""
    cursor = conn.cursor()
    posts = cursor.execute('''
        SELECT post_id, COUNT(*) as comment_count
        FROM comments
        GROUP BY post_id
        ORDER BY comment_count DESC
    ''').fetchall()
    return posts

def get_post_comments(conn, post_id):
    """Get all comments for a specific post."""
    cursor = conn.cursor()
    comments = cursor.execute('''
        SELECT id, parent_id, author_name, content, created_at, status
        FROM comments
        WHERE post_id = ?
        ORDER BY created_at ASC
    ''', [post_id]).fetchall()
    return comments

def set_parent(conn, comment_id, parent_id):
    """Set the parent of a comment."""
    cursor = conn.cursor()
    cursor.execute('UPDATE comments SET parent_id = ? WHERE id = ?', [parent_id, comment_id])
    conn.commit()
    print(f"✅ Set comment {comment_id} as a reply to comment {parent_id}")

def display_comments(comments):
    """Display all comments with IDs and content."""
    print("\nAll comments for this post:")
    print("=" * 80)
    for comment in comments:
        created_at = datetime.fromisoformat(comment['created_at']).strftime("%Y-%m-%d %H:%M")
        parent_info = f" (reply to #{comment['parent_id']})" if comment['parent_id'] else ""
        
        print(f"ID: {comment['id']}{parent_info} | {created_at} | {comment['author_name']}")
        content = comment['content'].replace('\n', ' ')
        wrapped_content = textwrap.fill(content, width=75, initial_indent="  ", subsequent_indent="  ")
        print(wrapped_content)
        print("-" * 80)
    print("=" * 80)

def process_post(conn, post_id):
    """Process a single post, allowing manual parent-child association."""
    print(f"\nProcessing post: {post_id}")
    
    # Get all comments for this post
    comments = get_post_comments(conn, post_id)
    if not comments:
        print("No comments found for this post.")
        return
    
    # Display all comments
    display_comments(comments)
    
    # Create lookup dictionary for quick comment retrieval
    comment_dict = {c['id']: c for c in comments}
    
    print("\nInstructions:")
    print("- To set a parent-child relationship: 'set CHILD_ID PARENT_ID'")
    print("- To remove a parent-child relationship: 'clear COMMENT_ID'")
    print("- To finish with this post: 'done'")
    print("- To exit the program: 'exit'")
    
    while True:
        command = input("\nEnter command: ").strip()
        
        if command.lower() == 'done':
            break
        elif command.lower() == 'exit':
            sys.exit(0)
        elif command.startswith('set '):
            try:
                parts = command.split()
                if len(parts) != 3:
                    print("Invalid format. Use 'set CHILD_ID PARENT_ID'")
                    continue
                
                child_id = int(parts[1])
                parent_id = int(parts[2])
                
                if child_id not in comment_dict:
                    print(f"Error: Comment ID {child_id} not found")
                    continue
                    
                if parent_id not in comment_dict:
                    print(f"Error: Parent ID {parent_id} not found")
                    continue
                    
                if child_id == parent_id:
                    print("Error: A comment cannot be its own parent")
                    continue
                
                # Set the parent-child relationship
                set_parent(conn, child_id, parent_id)
                
                # Update local data
                comments = get_post_comments(conn, post_id)
                comment_dict = {c['id']: c for c in comments}
                
                # Show updated comments
                display_comments(comments)
                
            except ValueError:
                print("Error: IDs must be numbers")
                
        elif command.startswith('clear '):
            try:
                parts = command.split()
                if len(parts) != 2:
                    print("Invalid format. Use 'clear COMMENT_ID'")
                    continue
                    
                comment_id = int(parts[1])
                if comment_id not in comment_dict:
                    print(f"Error: Comment ID {comment_id} not found")
                    continue
                
                # Clear parent relationship
                cursor = conn.cursor()
                cursor.execute('UPDATE comments SET parent_id = NULL WHERE id = ?', [comment_id])
                conn.commit()
                print(f"✅ Cleared parent relationship for comment {comment_id}")
                
                # Update local data
                comments = get_post_comments(conn, post_id)
                comment_dict = {c['id']: c for c in comments}
                
                # Show updated comments
                display_comments(comments)
                
            except ValueError:
                print("Error: ID must be a number")
        else:
            print("Unknown command. Try again.")

def main():
    """Main entry point for the script."""
    db_path = '../comments.sqlite'
    
    # Allow custom database path
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    # Connect to database
    conn = connect_to_db(db_path)
    
    # Get all posts with comments
    posts = get_all_posts(conn)
    if not posts:
        print("No posts with comments found in the database.")
        return
    
    print(f"Found {len(posts)} posts with comments:\n")
    for i, post in enumerate(posts):
        print(f"{i+1}. {post['post_id']} ({post['comment_count']} comments)")
    
    # Process each post in a loop
    while True:
        post_input = input("\nEnter post number, post ID, 'all', or 'exit': ").strip()
        
        if post_input.lower() == 'exit':
            break
            
        if post_input.lower() == 'all':
            for post in posts:
                process_post(conn, post['post_id'])
            break
            
        try:
            if post_input.isdigit() and 1 <= int(post_input) <= len(posts):
                # User entered a post number
                selected_post = posts[int(post_input) - 1]
                process_post(conn, selected_post['post_id'])
            else:
                # User entered a post ID directly
                post_id = post_input
                if not any(p['post_id'] == post_id for p in posts):
                    print(f"Warning: No comments found for post '{post_id}'")
                    continue
                process_post(conn, post_id)
        except ValueError:
            print("Invalid input. Please enter a valid post number or ID.")
    
    conn.close()
    print("Done! Comment hierarchies updated.")

if __name__ == "__main__":
    main()
