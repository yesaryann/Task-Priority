# Smart Task Analyzer

A Django-based task management system that intelligently scores and prioritizes tasks based on multiple factors including urgency, importance, effort, and dependencies.

## Overview

The Smart Task Analyzer helps users identify which tasks they should work on first by calculating priority scores using a sophisticated algorithm. The system supports multiple sorting strategies to accommodate different work styles and priorities.

## Features

- **Intelligent Priority Scoring**: Calculates task priority based on urgency, importance, effort, and dependencies
- **Multiple Sorting Strategies**: 
  - Smart Balance: Balanced algorithm considering all factors
  - Fastest Wins: Prioritize low-effort tasks for quick wins
  - High Impact: Prioritize high importance tasks
  - Deadline Driven: Prioritize based on due dates
- **Circular Dependency Detection**: Automatically detects and flags circular dependencies
- **User-Friendly Interface**: Clean, responsive web interface for task management
- **Bulk Import**: Import multiple tasks via JSON format
- **Visual Priority Indicators**: Color-coded priority levels (High/Medium/Low)

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or download this repository**

2. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

3. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   ```

4. **Activate the virtual environment:**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

5. **Install dependencies:**
   ```bash
   pip install -r ../requirements.txt
   ```

6. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

7. **Start the Django development server:**
   ```bash
   python manage.py runserver
   ```
   The API will be available at `http://localhost:8000`

### Running the Frontend

1. **Open the frontend files:**
   - Simply open `frontend/index.html` in a web browser, or
   - Use a local web server (e.g., Python's http.server, Live Server extension in VS Code)

2. **If using a simple HTTP server:**
   ```bash
   cd frontend
   python -m http.server 5500
   ```
   Then navigate to `http://localhost:5500` in your browser

3. **Note:** Make sure the Django backend is running on `http://localhost:8000` for the frontend to communicate with the API.

## Algorithm Explanation

The priority scoring algorithm evaluates tasks based on four key factors, each contributing to the final priority score:

### 1. Urgency Score (40% weight in Smart Balance)

The urgency score is calculated based on the task's due date relative to today:
- **Past due tasks**: Receive exponentially increasing urgency scores (0.9-1.0) with penalties based on how many days overdue
- **Due today**: Maximum urgency score of 1.0
- **Due tomorrow**: Very high urgency (0.95)
- **Due in 3 days**: High urgency (0.85)
- **Due in 7 days**: Moderate-high urgency using exponential decay
- **Due in 14 days**: Moderate urgency
- **Due in 30+ days**: Low urgency with exponential decay
- **No due date**: Neutral score of 0.5

The algorithm uses exponential decay functions to create smooth transitions between urgency levels, ensuring that tasks become progressively more urgent as their deadlines approach.

### 2. Importance Score (30% weight in Smart Balance)

The importance score normalizes the user-provided importance rating (1-10 scale) to a 0-1 scale:
- **Importance 10**: Score of 1.0 (maximum)
- **Importance 1**: Score of 0.0 (minimum)
- **Importance 5**: Score of approximately 0.44 (middle)
- **Invalid values**: Automatically clamped to the 1-10 range

This linear normalization ensures that higher importance ratings directly translate to higher priority scores.

### 3. Effort Score (20% weight in Smart Balance)

The effort score uses an inverse relationship - lower effort tasks receive higher scores:
- **<1 hour**: Score of 1.0 (very quick task)
- **1-2 hours**: Score of 0.9
- **2-4 hours**: Score of 0.75
- **4-8 hours**: Score of 0.6
- **8-16 hours**: Score of 0.4
- **16-40 hours**: Score of 0.25
- **>40 hours**: Score decreases exponentially
- **No estimate**: Neutral score of 0.5

This encourages "quick wins" by prioritizing tasks that can be completed quickly, which can boost productivity and momentum.

### 4. Dependency Score (10% weight in Smart Balance)

The dependency score evaluates how many other tasks depend on the current task:
- **0 dependents**: Score of 0.3 (lower priority)
- **1 dependent**: Score of 0.6 (moderate priority)
- **2-3 dependents**: Score of 0.8 (high priority)
- **4+ dependents**: Score of 1.0 (very high priority - blocking)

This ensures that tasks that block other work are prioritized appropriately, preventing bottlenecks in task completion.

### Strategy-Specific Algorithms

**Smart Balance**: Combines all four factors with weights (40% urgency, 30% importance, 20% effort, 10% dependencies)

**Fastest Wins**: Emphasizes effort (80%) with some urgency consideration (20%)

**High Impact**: Emphasizes importance (70%) with urgency (30%)

**Deadline Driven**: Emphasizes urgency (90%) with minimal importance (10%)

### Circular Dependency Detection

The system uses a depth-first search (DFS) algorithm to detect circular dependencies. When a task depends on another task that eventually depends back on the original task, the system flags these tasks and includes them in the circular dependency chain information.

## Design Decisions

### Weight Distribution

The default weights in the Smart Balance strategy (40% urgency, 30% importance, 20% effort, 10% dependencies) were chosen based on the following reasoning:

1. **Urgency (40%)**: Deadlines are often externally imposed and non-negotiable, making them critical for task prioritization
2. **Importance (30%)**: User-defined importance reflects business value and should have significant weight
3. **Effort (20%)**: Quick wins can boost productivity, but shouldn't override critical deadlines or important work
4. **Dependencies (10%)**: While important for workflow, dependencies are less critical than direct task characteristics

These weights can be adjusted based on organizational needs, but provide a balanced default that works well for most scenarios.

### Edge Case Handling

1. **Missing Data**: Tasks with missing due dates or effort estimates receive neutral scores (0.5) for those factors, ensuring they can still be prioritized based on available information
2. **Past Due Dates**: Overdue tasks receive exponentially increasing urgency scores to ensure they're prioritized appropriately
3. **Invalid Importance**: Values outside 1-10 are automatically clamped to the valid range
4. **Circular Dependencies**: Detected and flagged, but don't prevent scoring - users are warned but can still prioritize tasks

### Trade-offs

1. **Simplicity vs. Complexity**: The algorithm balances sophistication with understandability - complex enough to be useful, simple enough to explain
2. **Configurability**: While the algorithm supports different strategies, weights are currently hardcoded. A future enhancement could allow user-customizable weights
3. **Real-time vs. Batch**: The current implementation processes tasks in batch. For very large task lists, incremental updates could improve performance

## Time Breakdown

- **Project Setup & Django Configuration**: 30 minutes
- **Task Model & Database**: 20 minutes
- **Core Scoring Algorithm**: 1.5 hours
  - Urgency calculation: 25 minutes
  - Importance normalization: 10 minutes
  - Effort calculation: 15 minutes
  - Dependency scoring: 20 minutes
  - Strategy implementations: 20 minutes
- **Circular Dependency Detection**: 30 minutes
- **API Endpoints & Serializers**: 45 minutes
- **Frontend HTML Structure**: 30 minutes
- **Frontend JavaScript & API Integration**: 1 hour
- **CSS Styling & Responsive Design**: 45 minutes
- **Unit Tests**: 45 minutes
- **Documentation**: 30 minutes

**Total Estimated Time**: ~6.5 hours

## API Endpoints

### POST `/api/tasks/analyze/`

Analyzes and sorts tasks by priority score.

**Request Body:**
```json
{
  "tasks": [
    {
      "title": "Fix login bug",
      "due_date": "2025-11-30",
      "estimated_hours": 3,
      "importance": 8,
      "dependencies": []
    }
  ],
  "strategy": "smart_balance"
}
```

**Response:**
```json
{
  "tasks": [
    {
      "id": "task1",
      "title": "Fix login bug",
      "due_date": "2025-11-30",
      "estimated_hours": 3,
      "importance": 8,
      "dependencies": [],
      "priority_score": 0.8234,
      "explanation": "Smart Balance: Due in X days...",
      "has_circular_dependency": false
    }
  ],
  "strategy_used": "smart_balance",
  "total_tasks": 1
}
```

### GET `/api/tasks/suggest/`

Returns the top 3 tasks to work on today.

**Query Parameters:**
- `tasks`: JSON array of tasks (URL-encoded)
- `strategy`: Sorting strategy (optional, default: "smart_balance")

## Future Improvements

Given more time, I would implement:

1. **User Authentication**: Allow users to save and manage their task lists
2. **Customizable Weights**: Let users adjust the weight distribution in Smart Balance strategy
3. **Task History**: Track task completion and learn from user behavior
4. **Date Intelligence**: Consider weekends and holidays when calculating urgency
5. **Eisenhower Matrix Visualization**: Display tasks on a 2D grid (Urgent vs Important)
6. **Dependency Graph Visualization**: Visual representation of task dependencies
7. **Task Templates**: Pre-defined task templates for common workflows
8. **Export/Import**: Export prioritized task lists to various formats (CSV, JSON, iCal)
9. **Notifications**: Remind users about high-priority tasks
10. **Performance Optimization**: Caching and optimization for large task lists (1000+ tasks)

## Testing

Run the test suite with:
```bash
cd backend
python manage.py test tasks
```

The test suite includes:
- Normal task scoring scenarios
- Edge cases (missing data, past due dates, invalid inputs)
- Circular dependency detection
- Different sorting strategies
- Individual component tests (urgency, importance, effort, dependencies)

## License

This project is created for assessment purposes.

## Contact

For questions or issues, please refer to the repository or contact the development team.

