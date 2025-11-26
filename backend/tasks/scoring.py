"""
Priority scoring algorithm for tasks.
Handles urgency, importance, effort, and dependency calculations.
"""
from datetime import date, datetime
from typing import List, Dict, Tuple, Optional
import math


def detect_circular_dependencies(tasks: List[Dict]) -> List[List[str]]:
    """
    Detect circular dependencies in a list of tasks using DFS.
    
    Args:
        tasks: List of task dictionaries with 'id' and 'dependencies' fields
        
    Returns:
        List of circular dependency chains (each chain is a list of task IDs)
    """
    # Build adjacency list
    graph = {}
    task_ids = set()
    
    for task in tasks:
        task_id = str(task.get('id', task.get('title', '')))
        task_ids.add(task_id)
        graph[task_id] = [str(dep) for dep in task.get('dependencies', [])]
    
    # DFS to detect cycles
    visited = set()
    rec_stack = set()
    cycles = []
    
    def dfs(node: str, path: List[str]) -> None:
        if node in rec_stack:
            # Found a cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return
        
        if node in visited:
            return
        
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor in task_ids:
                dfs(neighbor, path.copy())
        
        rec_stack.remove(node)
    
    for task_id in task_ids:
        if task_id not in visited:
            dfs(task_id, [])
    
    return cycles


def calculate_urgency_score(due_date: Optional[str], current_date: Optional[date] = None) -> Tuple[float, str]:
    """
    Calculate urgency score based on due date.
    
    Args:
        due_date: Due date as string (YYYY-MM-DD) or None
        current_date: Current date for comparison (defaults to today)
        
    Returns:
        Tuple of (score, explanation)
    """
    if current_date is None:
        current_date = date.today()
    
    if not due_date:
        return 0.5, "No due date specified - neutral urgency"
    
    try:
        if isinstance(due_date, str):
            due = datetime.strptime(due_date, '%Y-%m-%d').date()
        else:
            due = due_date
        
        days_until_due = (due - current_date).days
        
        if days_until_due < 0:
            # Past due - high urgency with penalty
            days_overdue = abs(days_until_due)
            # Exponential penalty for overdue tasks
            score = min(1.0, 0.9 + (0.1 * (1 - math.exp(-days_overdue / 7))))
            return score, f"Overdue by {days_overdue} day(s) - high priority"
        
        elif days_until_due == 0:
            return 1.0, "Due today - highest urgency"
        
        elif days_until_due <= 1:
            return 0.95, "Due tomorrow - very high urgency"
        
        elif days_until_due <= 3:
            return 0.85, "Due in 3 days - high urgency"
        
        elif days_until_due <= 7:
            # Exponential decay for near-term tasks
            score = 0.7 + (0.15 * math.exp(-(days_until_due - 3) / 4))
            return score, f"Due in {days_until_due} days - moderate-high urgency"
        
        elif days_until_due <= 14:
            score = 0.5 + (0.2 * math.exp(-(days_until_due - 7) / 7))
            return score, f"Due in {days_until_due} days - moderate urgency"
        
        elif days_until_due <= 30:
            score = 0.3 + (0.2 * math.exp(-(days_until_due - 14) / 16))
            return score, f"Due in {days_until_due} days - low-moderate urgency"
        
        else:
            # Far future - low urgency
            score = max(0.1, 0.3 * math.exp(-(days_until_due - 30) / 30))
            return score, f"Due in {days_until_due} days - low urgency"
    
    except (ValueError, TypeError):
        return 0.5, "Invalid due date format - neutral urgency"


def calculate_importance_score(importance: Optional[int]) -> Tuple[float, str]:
    """
    Normalize importance (1-10) to 0-1 scale.
    
    Args:
        importance: Importance rating (1-10) or None
        
    Returns:
        Tuple of (score, explanation)
    """
    if importance is None:
        return 0.5, "No importance specified - neutral score"
    
    # Clamp to valid range
    importance = max(1, min(10, importance))
    
    # Normalize to 0-1 scale
    score = (importance - 1) / 9.0
    
    if importance >= 9:
        return score, f"Very high importance ({importance}/10)"
    elif importance >= 7:
        return score, f"High importance ({importance}/10)"
    elif importance >= 5:
        return score, f"Moderate importance ({importance}/10)"
    elif importance >= 3:
        return score, f"Low-moderate importance ({importance}/10)"
    else:
        return score, f"Low importance ({importance}/10)"


def calculate_effort_score(estimated_hours: Optional[float]) -> Tuple[float, str]:
    """
    Calculate effort score (inverse relationship - lower effort = higher score).
    
    Args:
        estimated_hours: Estimated hours to complete or None
        
    Returns:
        Tuple of (score, explanation)
    """
    if estimated_hours is None or estimated_hours <= 0:
        return 0.5, "No effort estimate - neutral score"
    
    # Normalize effort: lower hours = higher score
    # Using logarithmic scale to handle wide range of values
    if estimated_hours <= 1:
        score = 1.0
        desc = "Very quick task (<1 hour)"
    elif estimated_hours <= 2:
        score = 0.9
        desc = "Quick task (1-2 hours)"
    elif estimated_hours <= 4:
        score = 0.75
        desc = "Short task (2-4 hours)"
    elif estimated_hours <= 8:
        score = 0.6
        desc = "Medium task (4-8 hours)"
    elif estimated_hours <= 16:
        score = 0.4
        desc = "Long task (8-16 hours)"
    elif estimated_hours <= 40:
        score = 0.25
        desc = "Very long task (16-40 hours)"
    else:
        score = max(0.1, 0.25 * math.exp(-(estimated_hours - 40) / 40))
        desc = f"Extensive task ({estimated_hours} hours)"
    
    return score, desc


def calculate_dependency_score(task: Dict, all_tasks: List[Dict]) -> Tuple[float, str]:
    """
    Calculate dependency score based on how many tasks depend on this one.
    
    Args:
        task: Current task dictionary
        all_tasks: List of all task dictionaries
        
    Returns:
        Tuple of (score, explanation)
    """
    task_id = str(task.get('id', task.get('title', '')))
    
    # Count how many tasks depend on this task
    dependents = 0
    for other_task in all_tasks:
        other_deps = [str(dep) for dep in other_task.get('dependencies', [])]
        if task_id in other_deps:
            dependents += 1
    
    if dependents == 0:
        return 0.3, "No tasks depend on this - lower priority"
    elif dependents == 1:
        return 0.6, f"1 task depends on this - moderate priority"
    elif dependents <= 3:
        return 0.8, f"{dependents} tasks depend on this - high priority"
    else:
        return 1.0, f"{dependents} tasks depend on this - very high priority (blocking)"


def fastest_wins_score(task: Dict, all_tasks: List[Dict], current_date: Optional[date] = None) -> Tuple[float, str]:
    """
    Prioritize low-effort tasks (quick wins).
    
    Args:
        task: Task dictionary
        all_tasks: List of all tasks
        current_date: Current date for comparison
        
    Returns:
        Tuple of (score, explanation)
    """
    effort_score, effort_desc = calculate_effort_score(task.get('estimated_hours'))
    
    # Weight heavily towards effort (80%), with some urgency (20%)
    urgency_score, urgency_desc = calculate_urgency_score(task.get('due_date'), current_date)
    
    final_score = (effort_score * 0.8) + (urgency_score * 0.2)
    
    explanation = f"Fastest Wins: {effort_desc}. {urgency_desc}"
    
    return final_score, explanation


def high_impact_score(task: Dict, all_tasks: List[Dict], current_date: Optional[date] = None) -> Tuple[float, str]:
    """
    Prioritize importance over everything else.
    
    Args:
        task: Task dictionary
        all_tasks: List of all tasks
        current_date: Current date for comparison
        
    Returns:
        Tuple of (score, explanation)
    """
    importance_score, importance_desc = calculate_importance_score(task.get('importance'))
    
    # Weight heavily towards importance (70%), with some urgency (30%)
    urgency_score, urgency_desc = calculate_urgency_score(task.get('due_date'), current_date)
    
    final_score = (importance_score * 0.7) + (urgency_score * 0.3)
    
    explanation = f"High Impact: {importance_desc}. {urgency_desc}"
    
    return final_score, explanation


def deadline_driven_score(task: Dict, all_tasks: List[Dict], current_date: Optional[date] = None) -> Tuple[float, str]:
    """
    Prioritize based on due date (urgency).
    
    Args:
        task: Task dictionary
        all_tasks: List of all tasks
        current_date: Current date for comparison
        
    Returns:
        Tuple of (score, explanation)
    """
    urgency_score, urgency_desc = calculate_urgency_score(task.get('due_date'), current_date)
    
    # Weight heavily towards urgency (90%), with minimal importance (10%)
    importance_score, importance_desc = calculate_importance_score(task.get('importance'))
    
    final_score = (urgency_score * 0.9) + (importance_score * 0.1)
    
    explanation = f"Deadline Driven: {urgency_desc}. {importance_desc}"
    
    return final_score, explanation


def smart_balance_score(task: Dict, all_tasks: List[Dict], current_date: Optional[date] = None) -> Tuple[float, str]:
    """
    Balanced algorithm considering all factors with configurable weights.
    
    Default weights:
    - Urgency: 0.4
    - Importance: 0.3
    - Effort: 0.2
    - Dependencies: 0.1
    
    Args:
        task: Task dictionary
        all_tasks: List of all tasks
        current_date: Current date for comparison
        
    Returns:
        Tuple of (score, explanation)
    """
    urgency_score, urgency_desc = calculate_urgency_score(task.get('due_date'), current_date)
    importance_score, importance_desc = calculate_importance_score(task.get('importance'))
    effort_score, effort_desc = calculate_effort_score(task.get('estimated_hours'))
    dependency_score, dependency_desc = calculate_dependency_score(task, all_tasks)
    
    # Weighted combination
    final_score = (
        urgency_score * 0.4 +
        importance_score * 0.3 +
        effort_score * 0.2 +
        dependency_score * 0.1
    )
    
    explanation = f"Smart Balance: {urgency_desc}. {importance_desc}. {effort_desc}. {dependency_desc}"
    
    return final_score, explanation


def calculate_priority_score(
    task: Dict,
    all_tasks: List[Dict],
    strategy: str = 'smart_balance',
    current_date: Optional[date] = None
) -> Tuple[float, str]:
    """
    Calculate priority score for a task based on selected strategy.
    
    Args:
        task: Task dictionary with fields: title, due_date, estimated_hours, importance, dependencies
        all_tasks: List of all task dictionaries
        strategy: Scoring strategy ('fastest_wins', 'high_impact', 'deadline_driven', 'smart_balance')
        current_date: Current date for comparison (defaults to today)
        
    Returns:
        Tuple of (score, explanation)
    """
    strategy_map = {
        'fastest_wins': fastest_wins_score,
        'high_impact': high_impact_score,
        'deadline_driven': deadline_driven_score,
        'smart_balance': smart_balance_score,
    }
    
    scoring_func = strategy_map.get(strategy.lower(), smart_balance_score)
    
    return scoring_func(task, all_tasks, current_date)

