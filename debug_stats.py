#!/usr/bin/env python3
import sqlite3
import database

def debug_player_stats():
    """Debug function to check player statistics"""
    conn = sqlite3.connect('event_data.db')
    cursor = conn.cursor()
    
    # Get all players
    cursor.execute('SELECT discord_id, nickname FROM players')
    players = cursor.fetchall()
    
    print("=== DEBUG: Player Statistics ===")
    for discord_id, nickname in players:
        print(f"\nPlayer: {nickname} (ID: {discord_id})")
        
        # Check submissions directly from database
        cursor.execute('''
            SELECT submission_id, is_approved, submission_time 
            FROM submissions 
            WHERE player_id = ? 
            ORDER BY submission_time DESC
        ''', (discord_id,))
        
        submissions_raw = cursor.fetchall()
        print(f"Raw submissions from DB: {submissions_raw}")
        
        # Check submissions from database.py function
        submissions_func = database.get_player_submissions(discord_id)
        print(f"Submissions from function: {len(submissions_func)} items")
        
        for sub in submissions_func:
            print(f"  - ID: {sub['submission_id']}, is_approved: {sub['is_approved']} (type: {type(sub['is_approved'])})")
        
        # Calculate statistics (fixed to handle both integer and boolean values)
        approved_count = len([s for s in submissions_func if s['is_approved'] == 1 or s['is_approved'] is True])
        rejected_count = len([s for s in submissions_func if s['is_approved'] == 0 or s['is_approved'] is False])
        pending_count = len([s for s in submissions_func if s['is_approved'] is None])
        
        print(f"Stats: ✅{approved_count} ❌{rejected_count} ⏳{pending_count}")
    
    conn.close()

if __name__ == "__main__":
    debug_player_stats()