// API Configuration
const API_BASE_URL = 'http://localhost:8000/api/tasks';

// State
let tasks = [];

// DOM Elements
const taskForm = document.getElementById('task-form');
const bulkJsonInput = document.getElementById('bulk-json');
const loadJsonBtn = document.getElementById('load-json-btn');
const analyzeBtn = document.getElementById('analyze-btn');
const clearTasksBtn = document.getElementById('clear-tasks-btn');
const tasksList = document.getElementById('tasks-list');
const taskCount = document.getElementById('task-count');
const resultsContainer = document.getElementById('results-container');
const errorMessage = document.getElementById('error-message');
const loading = document.getElementById('loading');
const strategySelect = document.getElementById('strategy');
const strategyDescription = document.getElementById('strategy-description');

// Strategy descriptions
const strategyDescriptions = {
    smart_balance: 'balances everything - urgency, importance, effort, dependencies',
    fastest_wins: 'get the quick stuff done first',
    high_impact: 'focus on what matters most',
    deadline_driven: 'whatever is due soonest wins'
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    updateTaskList();
    updateStrategyDescription();
});

// Event Listeners
function setupEventListeners() {
    taskForm.addEventListener('submit', handleTaskFormSubmit);
    loadJsonBtn.addEventListener('click', handleLoadJson);
    analyzeBtn.addEventListener('click', handleAnalyze);
    clearTasksBtn.addEventListener('click', handleClearTasks);
    strategySelect.addEventListener('change', updateStrategyDescription);
}

function updateStrategyDescription() {
    const selectedStrategy = strategySelect.value;
    strategyDescription.textContent = strategyDescriptions[selectedStrategy] || '';
}

// Task Form Handling
function handleTaskFormSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(taskForm);
    const task = {
        title: formData.get('title').trim(),
        due_date: formData.get('due_date') || null,
        estimated_hours: formData.get('estimated_hours') ? parseFloat(formData.get('estimated_hours')) : null,
        importance: parseInt(formData.get('importance')) || 5,
        dependencies: parseDependencies(formData.get('dependencies'))
    };
    
    // Validate
    if (!task.title) {
        showError('Task title is required.');
        return;
    }
    
    if (task.importance < 1 || task.importance > 10) {
        showError('Importance must be between 1 and 10.');
        return;
    }
    
    // Add task
    tasks.push(task);
    updateTaskList();
    taskForm.reset();
    hideError();
}

function parseDependencies(depsString) {
    if (!depsString || !depsString.trim()) {
        return [];
    }
    return depsString.split(',').map(dep => dep.trim()).filter(dep => dep);
}

// Bulk JSON Loading
function handleLoadJson() {
    const jsonText = bulkJsonInput.value.trim();
    
    if (!jsonText) {
        showError('Please enter JSON data.');
        return;
    }
    
    try {
        const parsedTasks = JSON.parse(jsonText);
        const taskArray = Array.isArray(parsedTasks) ? parsedTasks : [parsedTasks];
        
        // Validate each task
        const validatedTasks = [];
        for (const task of taskArray) {
            if (!task.title) {
                showError('All tasks must have a title.');
                return;
            }
            
            // Normalize task
            const normalizedTask = {
                title: task.title,
                due_date: task.due_date || null,
                estimated_hours: task.estimated_hours || null,
                importance: task.importance || 5,
                dependencies: Array.isArray(task.dependencies) ? task.dependencies : []
            };
            
            validatedTasks.push(normalizedTask);
        }
        
        tasks = validatedTasks;
        updateTaskList();
        bulkJsonInput.value = '';
        hideError();
    } catch (error) {
        showError(`Invalid JSON format: ${error.message}`);
    }
}

// Task List Management
function updateTaskList() {
    taskCount.textContent = tasks.length;
    
    if (tasks.length === 0) {
        tasksList.innerHTML = '<p class="empty-tasks">no tasks yet</p>';
        return;
    }
    
    tasksList.innerHTML = tasks.map((task, index) => `
        <div class="task-item">
            <div class="task-item-header">
                <strong>${index + 1}. ${escapeHtml(task.title)}</strong>
                <button class="btn-remove" onclick="removeTask(${index})" title="Remove task">×</button>
            </div>
            <div class="task-item-details">
                ${task.due_date ? `<span>Due: ${task.due_date}</span>` : ''}
                ${task.estimated_hours ? `<span>Hours: ${task.estimated_hours}</span>` : ''}
                <span>Importance: ${task.importance}/10</span>
                ${task.dependencies.length > 0 ? `<span>Deps: ${task.dependencies.join(', ')}</span>` : ''}
            </div>
        </div>
    `).join('');
}

function removeTask(index) {
    tasks.splice(index, 1);
    updateTaskList();
}

function handleClearTasks() {
    if (tasks.length === 0) return;
    
    if (confirm('Are you sure you want to clear all tasks?')) {
        tasks = [];
        updateTaskList();
        resultsContainer.innerHTML = '<div class="empty-state"><p>Add tasks and click "Analyze Tasks" to see prioritized results.</p></div>';
    }
}

// API Integration
async function handleAnalyze() {
    if (tasks.length === 0) {
        showError('Please add at least one task before analyzing.');
        return;
    }
    
    hideError();
    showLoading();
    
    try {
        const strategy = strategySelect.value;
        const response = await fetch(`${API_BASE_URL}/analyze/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tasks: tasks,
                strategy: strategy
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze tasks');
        }
        
        displayResults(data);
    } catch (error) {
        showError(`Error analyzing tasks: ${error.message}. Make sure the Django server is running on http://localhost:8000`);
    } finally {
        hideLoading();
    }
}

// Results Display
function displayResults(data) {
    const { tasks: scoredTasks, strategy_used, circular_dependencies_detected } = data;
    
    if (scoredTasks.length === 0) {
        resultsContainer.innerHTML = '<div class="empty-state"><p>nothing to show</p></div>';
        return;
    }
    
    let html = `
        <div class="results-header">
            <p><strong>strategy:</strong> ${formatStrategyName(strategy_used)}</p>
            <p><strong>total tasks:</strong> ${scoredTasks.length}</p>
            ${circular_dependencies_detected ? '<p class="warning"><strong>⚠ heads up:</strong> found some circular dependencies</p>' : ''}
        </div>
    `;
    
    html += '<div class="tasks-results">';
    
    scoredTasks.forEach((task, index) => {
        const priorityLevel = getPriorityLevel(task.priority_score);
        const priorityClass = `priority-${priorityLevel}`;
        
        html += `
            <div class="task-card ${priorityClass}">
                    <div class="task-card-header">
                    <div class="task-rank">#${index + 1}</div>
                    <div class="task-title">${escapeHtml(task.title)}</div>
                    <div class="task-score">score: ${task.priority_score.toFixed(3)}</div>
                </div>
                
                <div class="task-card-body">
                    <div class="priority-badge ${priorityClass}">
                        ${priorityLevel} priority
                    </div>
                    
                    <div class="task-explanation">
                        <strong>why this one:</strong> ${escapeHtml(task.explanation)}
                    </div>
                    
                    <div class="task-details">
                        <div class="detail-item">
                            <span class="detail-label">due date:</span>
                            <span class="detail-value">${task.due_date || 'not set'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">estimated hours:</span>
                            <span class="detail-value">${task.estimated_hours || 'not set'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">importance:</span>
                            <span class="detail-value">${task.importance}/10</span>
                        </div>
                        ${task.dependencies.length > 0 ? `
                            <div class="detail-item">
                                <span class="detail-label">depends on:</span>
                                <span class="detail-value">${task.dependencies.join(', ')}</span>
                            </div>
                        ` : ''}
                    </div>
                    
                    ${task.has_circular_dependency ? `
                        <div class="circular-warning">
                            ⚠ this task has circular dependencies
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    
    resultsContainer.innerHTML = html;
}

function getPriorityLevel(score) {
    if (score >= 0.7) return 'high';
    if (score >= 0.4) return 'medium';
    return 'low';
}

function formatStrategyName(strategy) {
    const names = {
        smart_balance: 'smart balance',
        fastest_wins: 'fastest wins',
        high_impact: 'high impact',
        deadline_driven: 'deadline driven'
    };
    return names[strategy] || strategy;
}

// UI Helpers
function showLoading() {
    loading.classList.remove('hidden');
    analyzeBtn.disabled = true;
}

function hideLoading() {
    loading.classList.add('hidden');
    analyzeBtn.disabled = false;
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

function hideError() {
    errorMessage.classList.add('hidden');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

