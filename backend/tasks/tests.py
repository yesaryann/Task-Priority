from django.test import TestCase
from datetime import date, timedelta
from .scoring import (
    calculate_priority_score,
    calculate_urgency_score,
    calculate_importance_score,
    calculate_effort_score,
    calculate_dependency_score,
    detect_circular_dependencies,
    fastest_wins_score,
    high_impact_score,
    deadline_driven_score,
    smart_balance_score
)


class ScoringAlgorithmTests(TestCase):
    """Test cases for the priority scoring algorithm."""
    
    def setUp(self):
        """Set up test data."""
        self.today = date.today()
        self.tomorrow = self.today + timedelta(days=1)
        self.next_week = self.today + timedelta(days=7)
        self.last_week = self.today - timedelta(days=7)
    
    def test_normal_task_scoring(self):
        """Test 1: Normal task scoring with all factors present."""
        task = {
            'id': 'task1',
            'title': 'Complete project',
            'due_date': self.tomorrow.strftime('%Y-%m-%d'),
            'estimated_hours': 4,
            'importance': 8,
            'dependencies': []
        }
        
        all_tasks = [task]
        score, explanation = calculate_priority_score(task, all_tasks, strategy='smart_balance')
        
        # Score should be between 0 and 1
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1)
        
        # With high importance and near deadline, score should be relatively high
        self.assertGreater(score, 0.5)
        
        # Explanation should not be empty
        self.assertIsInstance(explanation, str)
        self.assertGreater(len(explanation), 0)
    
    def test_edge_cases_missing_data(self):
        """Test 2: Edge cases with missing dates, past due dates, invalid importance."""
        # Test missing due date
        task_no_date = {
            'id': 'task2',
            'title': 'Task without date',
            'due_date': None,
            'estimated_hours': 2,
            'importance': 5,
            'dependencies': []
        }
        
        score, explanation = calculate_priority_score(task_no_date, [task_no_date])
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1)
        self.assertIn('due date', explanation.lower())
        
        # Test past due date
        task_overdue = {
            'id': 'task3',
            'title': 'Overdue task',
            'due_date': self.last_week.strftime('%Y-%m-%d'),
            'estimated_hours': 3,
            'importance': 7,
            'dependencies': []
        }
        
        score, explanation = calculate_priority_score(task_overdue, [task_overdue])
        # Overdue tasks should have high urgency score
        self.assertGreater(score, 0.5)
        self.assertIn('overdue', explanation.lower() or 'past', explanation.lower())
        
        # Test missing estimated_hours
        task_no_hours = {
            'id': 'task4',
            'title': 'Task without hours',
            'due_date': self.next_week.strftime('%Y-%m-%d'),
            'estimated_hours': None,
            'importance': 6,
            'dependencies': []
        }
        
        score, explanation = calculate_priority_score(task_no_hours, [task_no_hours])
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1)
        
        # Test invalid importance (should be clamped)
        task_invalid_importance = {
            'id': 'task5',
            'title': 'Task with invalid importance',
            'due_date': self.tomorrow.strftime('%Y-%m-%d'),
            'estimated_hours': 5,
            'importance': 15,  # Invalid: > 10
            'dependencies': []
        }
        
        score, explanation = calculate_priority_score(task_invalid_importance, [task_invalid_importance])
        # Should still calculate a valid score (importance clamped to 10)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1)
    
    def test_circular_dependency_detection(self):
        """Test 3: Circular dependency detection."""
        # Create tasks with circular dependencies
        task_a = {
            'id': 'task_a',
            'title': 'Task A',
            'dependencies': ['task_b']
        }
        
        task_b = {
            'id': 'task_b',
            'title': 'Task B',
            'dependencies': ['task_c']
        }
        
        task_c = {
            'id': 'task_c',
            'title': 'Task C',
            'dependencies': ['task_a']  # Circular!
        }
        
        tasks = [task_a, task_b, task_c]
        cycles = detect_circular_dependencies(tasks)
        
        # Should detect at least one circular dependency
        self.assertGreater(len(cycles), 0)
        
        # Check that the cycle includes all three tasks
        found_cycle = False
        for cycle in cycles:
            if 'task_a' in cycle and 'task_b' in cycle and 'task_c' in cycle:
                found_cycle = True
                break
        
        self.assertTrue(found_cycle, "Should detect circular dependency between task_a, task_b, and task_c")
    
    def test_no_circular_dependencies(self):
        """Test that non-circular dependencies are not flagged."""
        task_a = {
            'id': 'task_a',
            'title': 'Task A',
            'dependencies': []
        }
        
        task_b = {
            'id': 'task_b',
            'title': 'Task B',
            'dependencies': ['task_a']
        }
        
        task_c = {
            'id': 'task_c',
            'title': 'Task C',
            'dependencies': ['task_b']
        }
        
        tasks = [task_a, task_b, task_c]
        cycles = detect_circular_dependencies(tasks)
        
        # Should not detect any circular dependencies
        self.assertEqual(len(cycles), 0)
    
    def test_different_sorting_strategies(self):
        """Test that different sorting strategies produce different scores."""
        task = {
            'id': 'task_strategy',
            'title': 'Test task',
            'due_date': self.tomorrow.strftime('%Y-%m-%d'),
            'estimated_hours': 2,
            'importance': 9,
            'dependencies': []
        }
        
        all_tasks = [task]
        
        # Test different strategies
        fastest_score, _ = fastest_wins_score(task, all_tasks)
        high_impact_score, _ = high_impact_score(task, all_tasks)
        deadline_score, _ = deadline_driven_score(task, all_tasks)
        smart_score, _ = smart_balance_score(task, all_tasks)
        
        # All scores should be valid
        for score in [fastest_score, high_impact_score, deadline_score, smart_score]:
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1)
        
        # Fastest wins should prioritize low effort (2 hours is low)
        self.assertGreater(fastest_score, 0.5)
        
        # High impact should prioritize importance (9 is high)
        self.assertGreater(high_impact_score, 0.5)
        
        # Deadline driven should prioritize urgency (tomorrow is urgent)
        self.assertGreater(deadline_score, 0.5)
    
    def test_dependency_scoring(self):
        """Test that tasks with more dependents get higher dependency scores."""
        blocking_task = {
            'id': 'blocking',
            'title': 'Blocking Task',
            'dependencies': []
        }
        
        dependent1 = {
            'id': 'dep1',
            'title': 'Dependent 1',
            'dependencies': ['blocking']
        }
        
        dependent2 = {
            'id': 'dep2',
            'title': 'Dependent 2',
            'dependencies': ['blocking']
        }
        
        dependent3 = {
            'id': 'dep3',
            'title': 'Dependent 3',
            'dependencies': ['blocking']
        }
        
        all_tasks = [blocking_task, dependent1, dependent2, dependent3]
        
        score, explanation = calculate_dependency_score(blocking_task, all_tasks)
        
        # Should have high dependency score (3 dependents)
        self.assertGreater(score, 0.7)
        self.assertIn('3 tasks', explanation)
        
        # Task with no dependents should have lower score
        isolated_task = {
            'id': 'isolated',
            'title': 'Isolated Task',
            'dependencies': []
        }
        
        isolated_score, isolated_explanation = calculate_dependency_score(isolated_task, all_tasks)
        self.assertLess(isolated_score, score)
    
    def test_urgency_calculation(self):
        """Test urgency score calculations for various scenarios."""
        # Due today
        score, explanation = calculate_urgency_score(self.today.strftime('%Y-%m-%d'))
        self.assertEqual(score, 1.0)
        self.assertIn('today', explanation.lower())
        
        # Past due
        past_date = (self.today - timedelta(days=5)).strftime('%Y-%m-%d')
        score, explanation = calculate_urgency_score(past_date)
        self.assertGreater(score, 0.8)
        self.assertIn('overdue', explanation.lower() or 'past', explanation.lower())
        
        # Far future
        far_future = (self.today + timedelta(days=60)).strftime('%Y-%m-%d')
        score, explanation = calculate_urgency_score(far_future)
        self.assertLess(score, 0.5)
        
        # No due date
        score, explanation = calculate_urgency_score(None)
        self.assertEqual(score, 0.5)
        self.assertIn('no due date', explanation.lower())
    
    def test_importance_calculation(self):
        """Test importance score normalization."""
        # Maximum importance
        score, explanation = calculate_importance_score(10)
        self.assertEqual(score, 1.0)
        
        # Minimum importance
        score, explanation = calculate_importance_score(1)
        self.assertEqual(score, 0.0)
        
        # Middle importance
        score, explanation = calculate_importance_score(5)
        self.assertAlmostEqual(score, 4/9, places=2)
        
        # Invalid importance (should be clamped)
        score, explanation = calculate_importance_score(15)
        self.assertEqual(score, 1.0)  # Clamped to 10, normalized to 1.0
        
        score, explanation = calculate_importance_score(0)
        self.assertEqual(score, 0.0)  # Clamped to 1, normalized to 0.0
    
    def test_effort_calculation(self):
        """Test effort score (inverse relationship)."""
        # Very quick task
        score, explanation = calculate_effort_score(0.5)
        self.assertGreater(score, 0.9)
        
        # Long task
        score, explanation = calculate_effort_score(40)
        self.assertLess(score, 0.3)
        
        # No effort specified
        score, explanation = calculate_effort_score(None)
        self.assertEqual(score, 0.5)

