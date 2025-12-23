"""
Review tracking utilities for managing reviewed fund-datagroup combinations.
Stores review data in a local text file.
"""

import os
import json
from datetime import datetime

REVIEW_FILE = "reviewed_items.txt"


def load_reviewed_items():
    """
    Load reviewed items from the text file.
    
    Returns:
        set: Set of tuples (fund_name, datagroup_name) that have been reviewed
    """
    if not os.path.exists(REVIEW_FILE):
        return set()
    
    reviewed = set()
    try:
        with open(REVIEW_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        reviewed.add((data['fund_name'], data['datagroup_name']))
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"Error loading reviewed items: {e}")
    
    return reviewed


def save_reviewed_item(fund_name, datagroup_name, reviewer_name):
    """
    Save a reviewed item to the text file. Always appends a new entry.
    
    Args:
        fund_name (str): Name of the fund
        datagroup_name (str): Name of the datagroup
        reviewer_name (str): Name of the person who reviewed
    """
    try:
        data = {
            'fund_name': fund_name,
            'datagroup_name': datagroup_name,
            'reviewer_name': reviewer_name,
            'reviewed_at': datetime.now().isoformat()
        }
        
        with open(REVIEW_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data) + '\n')
        
        return True
    except Exception as e:
        print(f"Error saving reviewed item: {e}")
        return False


def remove_reviewed_item(fund_name, datagroup_name):
    """
    Remove all reviewed entries for a item from the text file.
    
    Args:
        fund_name (str): Name of the fund
        datagroup_name (str): Name of the datagroup
    """
    try:
        if not os.path.exists(REVIEW_FILE):
            return True
            
        remaining_lines = []
        with open(REVIEW_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        if data['fund_name'] != fund_name or data['datagroup_name'] != datagroup_name:
                            remaining_lines.append(line)
                    except json.JSONDecodeError:
                        continue
        
        with open(REVIEW_FILE, 'w', encoding='utf-8') as f:
            for line in remaining_lines:
                f.write(line + '\n')
        
        return True
    except Exception as e:
        print(f"Error removing reviewed item: {e}")
        return False


def is_reviewed(fund_name, datagroup_name, reviewed_set):
    """
    Check if a fund-datagroup combination is reviewed.
    
    Args:
        fund_name (str): Name of the fund
        datagroup_name (str): Name of the datagroup
        reviewed_set (set): Set of reviewed items
        
    Returns:
        bool: True if reviewed, False otherwise
    """
    return (fund_name, datagroup_name) in reviewed_set


def get_review_details(fund_name, datagroup_name):
    """
    Get the latest review details for a specific fund-datagroup combination.
    
    Args:
        fund_name (str): Name of the fund
        datagroup_name (str): Name of the datagroup
        
    Returns:
        dict: Latest review details, or None if not found
    """
    if not os.path.exists(REVIEW_FILE):
        return None
    
    latest_data = None
    try:
        with open(REVIEW_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        if data['fund_name'] == fund_name and data['datagroup_name'] == datagroup_name:
                            latest_data = data
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"Error getting review details: {e}")
    
    return latest_data
