'use strict';

const State = {
  tasks: [],
  currentFilter: 'all',
  currentPriority: '',
  currentSort: 'created_at',
  editingTaskId: null,
  deletingTaskId: null,
  searchQuery: '',
};

const TASK_STATUSES = ['pending', 'in_progress', 'completed', 'cancelled'];

async function apiFetch(path, options = {}) {
  const defaults = {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
  };
  const res = await fetch(path, { ...defaults, ...options });
  const contentType = res.headers.get('content-type') || '';
  let data = null;

  if (contentType.includes('application/json')) {
    data = await res.json();
  } else {
    const text = await res.text();
    data = {
      success: res.ok,
      message: text || (res.ok ? 'Success' : 'Request failed.'),
    };
  }

  return { ok: res.ok, status: res.status, data };
}

let socket;

function upsertTask(task, { prepend = false } = {}) {
  const idx = State.tasks.findIndex(t => t.id === task.id);
  if (idx !== -1) {
    State.tasks[idx] = task;
    return;
  }

  if (prepend) {
    State.tasks.unshift(task);
  } else {
    State.tasks.push(task);
  }
}

function shouldShowTask(task) {
  if (State.currentFilter === 'all') {
    return task.status !== 'cancelled';
  }

  return task.status === State.currentFilter;
}

function syncTaskInCurrentView(task, { prepend = false } = {}) {
  if (shouldShowTask(task)) {
    upsertTask(task, { prepend });
  } else {
    State.tasks = State.tasks.filter(t => t.id !== task.id);
  }
}

function initSocket() {
  const ind = document.getElementById('wsIndicator');
  ind.classList.remove('connected');
  ind.classList.add('disconnected');

  socket = io({ transports: ['websocket', 'polling'] });

  socket.on('connect', () => {
    ind.classList.remove('disconnected');
    ind.classList.add('connected');
  });

  socket.on('disconnect', () => {
    ind.classList.remove('connected');
    ind.classList.add('disconnected');
  });

  socket.on('connect_error', () => {
    ind.classList.remove('connected');
    ind.classList.add('disconnected');
  });

  socket.on('task_created', (task) => {
    const hadTask = State.tasks.some(t => t.id === task.id);
    syncTaskInCurrentView(task, { prepend: true });
    renderTasks();
    loadAnalytics();
    if (!hadTask && shouldShowTask(task)) {
      showToast(`New task created: "${task.title}"`, 'info');
    }
  });

  socket.on('task_updated', (task) => {
    syncTaskInCurrentView(task);
    renderTasks();
    loadAnalytics();
  });

  socket.on('task_deleted', ({ id }) => {
    const had = State.tasks.find(t => t.id === id);
    if (had) {
      State.tasks = State.tasks.filter(t => t.id !== id);
      renderTasks();
      loadAnalytics();
    }
  });
}

async function loadTasks() {
  const skeleton = document.getElementById('taskSkeleton');
  skeleton.classList.remove('hidden');

  try {
    const params = new URLSearchParams();
    if (State.currentFilter !== 'all') params.set('status', State.currentFilter);
    if (State.currentPriority) params.set('priority', State.currentPriority);
    if (State.searchQuery) params.set('search', State.searchQuery);

    const { ok, data } = await apiFetch(`/api/tasks/?${params}`);
    if (ok) {
      State.tasks = data.data || [];
      renderTasks();
    } else {
      showToast('Failed to load tasks.', 'error');
    }
  } catch {
    showToast('Network error loading tasks.', 'error');
  } finally {
    skeleton.classList.add('hidden');
  }
}

async function loadAnalytics() {
  try {
    const { ok, data } = await apiFetch('/api/analytics/');
    if (ok) renderAnalytics(data.data);
  } catch {
    // Ignore analytics refresh errors in the background.
  }
}

function renderAnalytics(a) {
  if (!a) return;
  document.getElementById('statTotal').textContent = a.total_tasks;
  document.getElementById('statCompleted').textContent = a.completed_tasks;
  document.getElementById('statPending').textContent = a.pending_tasks;
  document.getElementById('statInProgress').textContent = a.in_progress_tasks;
  document.getElementById('statPct').textContent = `${a.completion_percentage}%`;
  document.getElementById('progressFill').style.width = `${a.completion_percentage}%`;
}

const PRIORITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };

function sortedTasks() {
  const arr = [...State.tasks];
  if (State.currentFilter === 'all') {
    arr.sort((a, b) => {
      const aDue = a.due_date ? new Date(a.due_date).getTime() : Number.POSITIVE_INFINITY;
      const bDue = b.due_date ? new Date(b.due_date).getTime() : Number.POSITIVE_INFINITY;
      if (aDue !== bDue) return aDue - bDue;

      const priorityDiff = (PRIORITY_ORDER[a.priority] ?? 9) - (PRIORITY_ORDER[b.priority] ?? 9);
      if (priorityDiff !== 0) return priorityDiff;

      return new Date(b.created_at) - new Date(a.created_at);
    });
  } else if (State.currentSort === 'priority') {
    arr.sort((a, b) => (PRIORITY_ORDER[a.priority] ?? 9) - (PRIORITY_ORDER[b.priority] ?? 9));
  } else {
    arr.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }
  return arr;
}

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDueDate(iso) {
  if (!iso) return 'No due date';
  const d = new Date(iso);
  return `Due ${d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}`;
}

function isTaskOverdue(task) {
  if (!task.due_date) return false;
  if (task.status === 'completed' || task.status === 'cancelled') return false;
  return new Date(task.due_date) < new Date();
}

function renderTasks() {
  const list = document.getElementById('taskList');
  const empty = document.getElementById('emptyState');
  const tasks = sortedTasks();

  list.querySelectorAll('.task-card').forEach(el => el.remove());

  if (tasks.length === 0) {
    empty.classList.remove('hidden');
    return;
  }
  empty.classList.add('hidden');

  tasks.forEach(task => {
    const card = document.createElement('div');
    card.className = 'task-card';
    card.dataset.id = task.id;
    card.dataset.priority = task.priority;
    card.dataset.status = task.status;
    const overdueClass = isTaskOverdue(task) ? ' task-chip--overdue' : '';
    const canEdit = task.status !== 'cancelled';
    const actionMarkup = canEdit
      ? `
        <label class="task-status-control" for="task-status-${task.id}">
          <span class="task-status-control__label">Status</span>
          <select class="task-status-select" id="task-status-${task.id}" data-id="${task.id}" aria-label="Change status for ${escHtml(task.title)}">
            ${TASK_STATUSES.map(status => `
              <option value="${status}" ${task.status === status ? 'selected' : ''}>${formatStatus(status)}</option>
            `).join('')}
          </select>
        </label>
        <button class="task-action-btn task-action-btn--edit" data-id="${task.id}" title="Edit">Edit</button>
      `
      : `
        <button class="task-restore-btn" data-id="${task.id}" title="Restore">Restore</button>
      `;

    card.innerHTML = `
      <div class="task-card__main">
        <span class="task-card__title">${escHtml(task.title)}</span>
        ${task.description ? `<span class="task-card__desc">${escHtml(task.description)}</span>` : ''}
        <div class="task-card__meta">
          <span class="badge badge--${task.priority}">Priority: ${formatStatus(task.priority)}</span>
          <span class="task-chip ${task.due_date ? 'task-chip--due' : ''}${overdueClass}">${escHtml(formatDueDate(task.due_date))}</span>
          <span class="task-date">Created ${formatDate(task.created_at)}</span>
        </div>
      </div>
      <div class="task-card__actions">
        ${actionMarkup}
        <button class="task-action-btn task-action-btn--delete" data-id="${task.id}" title="Delete">Delete</button>
      </div>`;

    list.appendChild(card);
  });
}

function formatStatus(s) {
  return s.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function openModal(id) {
  document.getElementById(id).classList.add('open');
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}

function resetTaskForm() {
  document.getElementById('taskTitle').value = '';
  document.getElementById('taskDesc').value = '';
  document.getElementById('taskPriority').value = 'medium';
  document.getElementById('taskDue').value = '';
  State.editingTaskId = null;
  document.getElementById('modalTitle').textContent = 'New Task';
  document.getElementById('saveTask').textContent = 'Save Task';
}

function populateTaskForm(task) {
  document.getElementById('taskTitle').value = task.title;
  document.getElementById('taskDesc').value = task.description || '';
  document.getElementById('taskPriority').value = task.priority;
  if (task.due_date) {
    const d = new Date(task.due_date);
    const pad = n => String(n).padStart(2, '0');
    document.getElementById('taskDue').value =
      `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }
  State.editingTaskId = task.id;
  document.getElementById('modalTitle').textContent = 'Edit Task';
  document.getElementById('saveTask').textContent = 'Update Task';
}

function openTaskEditor(taskId) {
  const task = State.tasks.find(t => t.id === taskId);
  if (!task) return;
  if (task.status === 'cancelled') {
    showToast('Restore this task before editing it.', 'info');
    return;
  }
  populateTaskForm(task);
  openModal('taskModal');
}

async function saveTask() {
  const title = document.getElementById('taskTitle').value.trim();
  if (!title) {
    showToast('Title is required.', 'error');
    return;
  }

  const payload = {
    title,
    description: document.getElementById('taskDesc').value.trim(),
    priority: document.getElementById('taskPriority').value,
    due_date: document.getElementById('taskDue').value || null,
  };

  const isEdit = !!State.editingTaskId;
  const path = isEdit ? `/api/tasks/${State.editingTaskId}` : '/api/tasks/';
  const method = isEdit ? 'PUT' : 'POST';

  try {
    const { ok, data } = await apiFetch(path, { method, body: JSON.stringify(payload) });
    if (ok) {
      showToast(isEdit ? 'Task updated.' : 'Task created.', 'success');
      closeModal('taskModal');

      syncTaskInCurrentView(data.data, { prepend: !isEdit });
      renderTasks();
      loadAnalytics();
    } else {
      showToast(data.message || 'Save failed.', 'error');
    }
  } catch {
    showToast('Network error.', 'error');
  }
}

async function deleteTask(id) {
  try {
    const { ok, data } = await apiFetch(`/api/tasks/${id}`, { method: 'DELETE' });
    if (ok) {
      showToast('Task deleted.', 'success');
      State.tasks = State.tasks.filter(t => t.id !== id);
      renderTasks();
      loadAnalytics();
    } else {
      showToast(data.message || 'Delete failed.', 'error');
    }
  } catch {
    showToast('Network error.', 'error');
  }
}

async function updateTaskStatus(id, newStatus) {
  const task = State.tasks.find(t => t.id === id);
  if (!task) return;
  if (task.status === newStatus) return;

  try {
    const { ok, data } = await apiFetch(`/api/tasks/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ status: newStatus }),
    });
    if (ok) {
      syncTaskInCurrentView(data.data);
      renderTasks();
      loadAnalytics();
      showToast(`Status changed to ${formatStatus(newStatus)}.`, 'success');
    } else {
      showToast(data.message || 'Status update failed.', 'error');
    }
  } catch {
    showToast('Network error.', 'error');
  }
}

async function restoreTask(id) {
  await updateTaskStatus(id, 'pending');
}

function wireEvents() {
  document.getElementById('sidebarToggle')?.addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
  });

  document.getElementById('newTaskBtn').addEventListener('click', () => {
    resetTaskForm();
    openModal('taskModal');
  });

  document.getElementById('closeModal').addEventListener('click', () => closeModal('taskModal'));
  document.getElementById('cancelModal').addEventListener('click', () => closeModal('taskModal'));
  document.getElementById('closeDeleteModal').addEventListener('click', () => closeModal('deleteModal'));
  document.getElementById('cancelDelete').addEventListener('click', () => closeModal('deleteModal'));

  document.getElementById('taskModal').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeModal('taskModal');
  });
  document.getElementById('deleteModal').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeModal('deleteModal');
  });

  document.getElementById('saveTask').addEventListener('click', saveTask);

  document.getElementById('confirmDelete').addEventListener('click', async () => {
    if (!State.deletingTaskId) return;
    closeModal('deleteModal');
    await deleteTask(State.deletingTaskId);
    State.deletingTaskId = null;
  });

  document.getElementById('taskList').addEventListener('click', e => {
    const editBtn = e.target.closest('.task-action-btn--edit');
    const deleteBtn = e.target.closest('.task-action-btn--delete');
    const restoreBtn = e.target.closest('.task-restore-btn');

    if (editBtn) {
      openTaskEditor(parseInt(editBtn.dataset.id));
    }
    if (restoreBtn) {
      restoreTask(parseInt(restoreBtn.dataset.id));
    }
    if (deleteBtn) {
      const id = parseInt(deleteBtn.dataset.id);
      const task = State.tasks.find(t => t.id === id);
      State.deletingTaskId = id;
      document.getElementById('deleteTaskName').textContent = task?.title ?? 'this task';
      openModal('deleteModal');
    }
  });

  document.getElementById('taskList').addEventListener('change', e => {
    const statusSelect = e.target.closest('.task-status-select');
    if (!statusSelect) return;
    updateTaskStatus(parseInt(statusSelect.dataset.id), statusSelect.value);
  });

  document.getElementById('taskList').addEventListener('dblclick', e => {
    if (e.target.closest('.task-card__actions')) return;
    const taskCard = e.target.closest('.task-card');
    if (!taskCard) return;
    openTaskEditor(parseInt(taskCard.dataset.id));
  });

  document.querySelectorAll('.nav-item[data-filter]').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('nav-item--active'));
      el.classList.add('nav-item--active');

      State.currentFilter = el.dataset.filter;
      const labels = {
        all: 'All Tasks',
        pending: 'Pending',
        in_progress: 'In Progress',
        completed: 'Completed',
        cancelled: 'Cancelled',
      };
      document.getElementById('sectionTitle').textContent = labels[State.currentFilter] ?? 'Tasks';

      document.getElementById('sidebar').classList.remove('open');
      loadTasks();
    });
  });

  document.getElementById('priorityFilter').addEventListener('change', e => {
    State.currentPriority = e.target.value;
    loadTasks();
  });

  document.querySelectorAll('.sort-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      State.currentSort = btn.dataset.sort;
      renderTasks();
    });
  });

  let searchTimer;
  document.getElementById('searchInput').addEventListener('input', e => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      State.searchQuery = e.target.value.trim();
      loadTasks();
    }, 350);
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeModal('taskModal');
      closeModal('deleteModal');
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  wireEvents();
  initSocket();
  loadTasks();
  loadAnalytics();
});
