"""
Utility for loading custom agent rules from text files.
"""
import os
from typing import Optional

def load_agent_rules(agent_name: str) -> str:
    """
    Load custom rules for a specific agent from its rules file.
    
    Args:
        agent_name: Name of the agent (e.g., 'auth', 'search', 'general')
        
    Returns:
        String containing custom rules, or empty string if file doesn't exist
    """
    rules_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agent_rules")
    rules_file = os.path.join(rules_dir, f"{agent_name}_agent_rules.txt")
    
    try:
        if os.path.exists(rules_file):
            with open(rules_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Filter out comments and empty lines
            rules = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    rules.append(line)
            
            if rules:
                return "\n\nCUSTOM RULES:\n" + "\n".join(f"- {rule}" for rule in rules)
        
        return ""
    except Exception as e:
        print(f"Warning: Could not load rules for {agent_name} agent: {e}")
        return ""


def get_rules_file_path(agent_name: str) -> str:
    """
    Get the full path to an agent's rules file.
    
    Args:
        agent_name: Name of the agent (e.g., 'auth', 'search', 'general')
        
    Returns:
        Full path to the rules file
    """
    rules_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agent_rules")
    return os.path.join(rules_dir, f"{agent_name}_agent_rules.txt")

