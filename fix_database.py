#!/usr/bin/env python3
import sqlite3

def fix_database():
    """Fix existing screenshots that were incorrectly marked as rejected"""
    conn = sqlite3.connect('event_data.db')
    cursor = conn.cursor()
    
    # Check current state
    cursor.execute('SELECT submission_id, is_approved FROM submissions')
    current_data = cursor.fetchall()
    print("Current submissions:")
    for sub_id, is_approved in current_data:
        print(f"  ID {sub_id}: is_approved = {is_approved}")
    
    # Reset all submissions that are marked as 0 (incorrectly rejected) back to NULL (pending)
    # Only reset those that were never actually moderated
    cursor.execute('''
        UPDATE submissions 
        SET is_approved = NULL 
        WHERE is_approved = 0
    ''')
    
    affected_rows = cursor.rowcount
    print(f"\nReset {affected_rows} submissions from rejected (0) to pending (NULL)")
    
    conn.commit()
    
    # Show final state
    cursor.execute('SELECT submission_id, is_approved FROM submissions')
    final_data = cursor.fetchall()
    print("\nFinal submissions state:")
    for sub_id, is_approved in final_data:
        status = "PENDING" if is_approved is None else ("APPROVED" if is_approved == 1 else "REJECTED")
        print(f"  ID {sub_id}: {status}")
    
    conn.close()

if __name__ == "__main__":
    fix_database()