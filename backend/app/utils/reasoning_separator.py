"""Utility to separate reasoning_breakdown and reasoning_notes"""
import re
from typing import Tuple


def auto_separate_reasoning(reasoning_breakdown: str, reasoning_notes: str) -> Tuple[str, str]:
    """
    Automatically separate reasoning_breakdown and reasoning_notes
    
    If reasoning_notes is empty but reasoning_breakdown contains paragraphs,
    split them into breakdown (bulleted lists) and notes (paragraphs).
    
    Args:
        reasoning_breakdown: Original breakdown content
        reasoning_notes: Original notes content
        
    Returns:
        Tuple of (separated_breakdown, separated_notes)
    """
    # If notes already exist or breakdown is empty, no need to separate
    if reasoning_notes or not reasoning_breakdown:
        return reasoning_breakdown, reasoning_notes
    
    # Split by double newlines to separate sections
    parts = reasoning_breakdown.split('\n\n')
    breakdown_parts = []
    notes_parts = []
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # If part starts with bullet point or dash, it's breakdown
        if part.startswith(('-', '*', '•', '・')) or re.match(r'^[\-\*•・]', part):
            breakdown_parts.append(part)
        # If part contains bullet points (multi-line list), it's breakdown
        elif '\n-' in part or '\n*' in part or '\n•' in part or '\n・' in part:
            breakdown_parts.append(part)
        # Otherwise, it's notes (paragraph)
        else:
            notes_parts.append(part)
    
    # If we found notes parts, separate them
    if notes_parts:
        separated_breakdown = '\n\n'.join(breakdown_parts)
        separated_notes = '\n\n'.join(notes_parts)
        return separated_breakdown, separated_notes
    
    # No separation needed
    return reasoning_breakdown, reasoning_notes
