from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import date
from typing import List, Dict
import json

from .serializers import TaskAnalyzeSerializer, TaskSerializer
from .scoring import calculate_priority_score, detect_circular_dependencies


@api_view(['POST'])
def analyze_tasks(request):
    """
    Analyze and sort tasks by priority score.
    
    Expected input:
    {
        "tasks": [
            {
                "title": "Task name",
                "due_date": "2025-11-30",
                "estimated_hours": 3,
                "importance": 8,
                "dependencies": []
            }
        ],
        "strategy": "smart_balance"  // optional: fastest_wins, high_impact, deadline_driven, smart_balance
    }
    """
    try:
        data = request.data
        
        # Get tasks and strategy
        tasks_data = data.get('tasks', [])
        strategy = data.get('strategy', 'smart_balance')
        
        if not tasks_data:
            return Response(
                {'error': 'No tasks provided. Please provide a list of tasks.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(tasks_data, list):
            return Response(
                {'error': 'Tasks must be provided as a list/array.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate strategy
        valid_strategies = ['fastest_wins', 'high_impact', 'deadline_driven', 'smart_balance']
        if strategy not in valid_strategies:
            return Response(
                {'error': f'Invalid strategy. Must be one of: {", ".join(valid_strategies)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate and normalize tasks
        validated_tasks = []
        for idx, task_data in enumerate(tasks_data):
            # Add id if not present (use index or title)
            if 'id' not in task_data:
                task_data['id'] = str(task_data.get('title', f'task_{idx}'))
            
            serializer = TaskAnalyzeSerializer(data=task_data)
            if not serializer.is_valid():
                return Response(
                    {
                        'error': f'Invalid task at index {idx}',
                        'details': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            validated_tasks.append(serializer.validated_data)
        
        # Detect circular dependencies
        circular_deps = detect_circular_dependencies(validated_tasks)
        circular_task_ids = set()
        for cycle in circular_deps:
            circular_task_ids.update(cycle)
        
        # Calculate scores for each task
        current_date = date.today()
        scored_tasks = []
        
        for task in validated_tasks:
            task_id = str(task.get('id', task.get('title', '')))
            score, explanation = calculate_priority_score(
                task,
                validated_tasks,
                strategy=strategy,
                current_date=current_date
            )
            
            # Find circular dependency chains involving this task
            task_circular_chains = [cycle for cycle in circular_deps if task_id in cycle]
            
            scored_task = {
                'id': task_id,
                'title': task.get('title'),
                'due_date': task.get('due_date'),
                'estimated_hours': task.get('estimated_hours'),
                'importance': task.get('importance', 5),
                'dependencies': task.get('dependencies', []),
                'priority_score': round(score, 4),
                'explanation': explanation,
                'has_circular_dependency': task_id in circular_task_ids,
                'circular_dependency_chain': task_circular_chains if task_circular_chains else []
            }
            
            scored_tasks.append(scored_task)
        
        # Sort by priority score (descending)
        scored_tasks.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Serialize response
        serializer = TaskSerializer(scored_tasks, many=True)
        
        return Response({
            'tasks': serializer.data,
            'strategy_used': strategy,
            'total_tasks': len(scored_tasks),
            'circular_dependencies_detected': len(circular_deps) > 0,
            'circular_dependency_count': len(circular_deps)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'An error occurred while analyzing tasks: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def suggest_tasks(request):
    """
    Return top 3 tasks the user should work on today.
    
    Accepts tasks as query parameter or uses sample tasks.
    Query parameter: ?tasks=[{...}] (URL-encoded JSON)
    """
    try:
        # Get tasks from query parameter or use sample
        tasks_param = request.query_params.get('tasks', None)
        
        if tasks_param:
            try:
                tasks_data = json.loads(tasks_param)
                if not isinstance(tasks_data, list):
                    tasks_data = [tasks_data]
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Invalid JSON format in tasks parameter.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Return sample response if no tasks provided
            return Response({
                'suggestions': [],
                'message': 'No tasks provided. Use POST /api/tasks/analyze/ to analyze tasks, or provide tasks as query parameter.',
                'example_usage': 'GET /api/tasks/suggest/?tasks=[{"title":"Task 1","importance":8,"due_date":"2025-11-30"}]'
            }, status=status.HTTP_200_OK)
        
        # Validate tasks
        validated_tasks = []
        for idx, task_data in enumerate(tasks_data):
            if 'id' not in task_data:
                task_data['id'] = str(task_data.get('title', f'task_{idx}'))
            
            serializer = TaskAnalyzeSerializer(data=task_data)
            if not serializer.is_valid():
                return Response(
                    {
                        'error': f'Invalid task at index {idx}',
                        'details': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            validated_tasks.append(serializer.validated_data)
        
        # Get strategy (default to smart_balance)
        strategy = request.query_params.get('strategy', 'smart_balance')
        
        # Calculate scores
        current_date = date.today()
        scored_tasks = []
        
        for task in validated_tasks:
            task_id = str(task.get('id', task.get('title', '')))
            score, explanation = calculate_priority_score(
                task,
                validated_tasks,
                strategy=strategy,
                current_date=current_date
            )
            
            scored_task = {
                'id': task_id,
                'title': task.get('title'),
                'due_date': task.get('due_date'),
                'estimated_hours': task.get('estimated_hours'),
                'importance': task.get('importance', 5),
                'dependencies': task.get('dependencies', []),
                'priority_score': round(score, 4),
                'explanation': explanation,
                'has_circular_dependency': False,
                'circular_dependency_chain': []
            }
            
            scored_tasks.append(scored_task)
        
        # Sort by priority score and get top 3
        scored_tasks.sort(key=lambda x: x['priority_score'], reverse=True)
        top_3 = scored_tasks[:3]
        
        # Create suggestions with explanations
        suggestions = []
        for i, task in enumerate(top_3, 1):
            suggestions.append({
                'rank': i,
                'task': task,
                'reason': f"Ranked #{i} with priority score {task['priority_score']}. {task['explanation']}"
            })
        
        return Response({
            'suggestions': suggestions,
            'strategy_used': strategy,
            'total_tasks_analyzed': len(validated_tasks)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'An error occurred while suggesting tasks: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

