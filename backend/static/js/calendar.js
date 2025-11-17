document.addEventListener('DOMContentLoaded', () => {
    const dayModal = document.getElementById('dayModal');
    const modalDate = document.getElementById('modalDate');
    const closeModal = document.querySelector('.close');
    const tasksContainer = document.getElementById('tasksContainer');

    // --- Відкриття модалки по кліку на день ---
    document.querySelectorAll('.day').forEach(day => {
        day.addEventListener('click', () => {
            modalDate.textContent = day.dataset.date;
            dayModal.dataset.currentDate = day.dataset.date;
            dayModal.style.display = 'flex';
            loadTasks(day.dataset.date);
        });
    });

    // --- Закриття модалки ---
    closeModal.addEventListener('click', () => {
        dayModal.style.display = 'none';
    });

    // --- Drag & Drop для завдань ---
    let draggedTask = null;

    function makeTaskDraggable(task) {
        task.draggable = true;
        task.addEventListener('dragstart', e => {
            draggedTask = task;
            e.dataTransfer.effectAllowed = 'move';
        });
    }

    function enableDropZone(dayElem) {
        dayElem.addEventListener('dragover', e => e.preventDefault());
        dayElem.addEventListener('drop', e => {
            e.preventDefault();
            if (draggedTask) {
                const taskId = draggedTask.dataset.id;
                const newDate = dayElem.dataset.date;
                fetch(`/planner/move_task/${taskId}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({new_date: newDate})
                }).then(() => location.reload());
                draggedTask = null;
            }
        });
    }

    document.querySelectorAll('.day').forEach(enableDropZone);

    // --- Завантаження завдань ---
    function loadTasks(date) {
        console.log('=== LOAD_TASKS STARTED ===');
        console.log('Date param:', date);
        console.log('Type:', typeof date);
        
        const list = qs('#panelTasks');
        const count = qs('#tasksCount');
        
        console.log('Panel tasks element exists:', !!list);
        console.log('Tasks count element exists:', !!count);
        
        if (!list || !count) {
            console.error('❌ CRITICAL: Missing DOM elements!');
            console.error('  #panelTasks:', list);
            console.error('  #tasksCount:', count);
            return;
        }
        
        // Показуємо loading стан
        list.innerHTML = '<div class="empty">⏳ Завантаження...</div>';
        
        // Формуємо правильну дату для запиту
        let formattedDate = date;
        if (date instanceof Date) {
            formattedDate = date.toISOString().slice(0, 10);
        }
        
        const url = `/planner/get_tasks/${formattedDate}`;
        console.log('Fetch URL:', url);
        
        fetch(url)
            .then(response => {
                console.log('Response status:', response.status);
                console.log('Response ok:', response.ok);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                return response.json();
            })
            .then(tasks => {
                console.log('=== RESPONSE RECEIVED ===');
                console.log('Tasks data:', tasks);
                console.log('Is array:', Array.isArray(tasks));
                console.log('Length:', tasks?.length);
                
                // Очищуємо список
                list.innerHTML = '';
                
                // Якщо це помилка від сервера
                if (tasks.error) {
                    console.error('Server error:', tasks.error);
                    list.innerHTML = `<div class="empty" style="color: #ff6b6b;">❌ Помилка: ${tasks.error}</div>`;
                    return;
                }
                
                // Якщо завдань немає
                if (!tasks || tasks.length === 0) {
                    console.log('✅ No tasks for this date');
                    list.innerHTML = '<div class="empty">📝 Немає задач на цей день<br><small>Перейдіть на вкладку "Створити" щоб додати</small></div>';
                    count.textContent = '0';
                    return;
                }
                
                console.log(`✅ Found ${tasks.length} tasks, creating rows...`);
                count.textContent = tasks.length;
                
                // Створюємо рядки для кожного завдання
                tasks.forEach((task, index) => {
                    console.log(`Creating row ${index + 1}:`, {
                        id: task._id,
                        title: task.title,
                        time: task.time,
                        completed: task.is_completed
                    });
                    
                    const row = document.createElement('div');
                    row.className = 'panel-task-row';
                    
                    if (task.category) {
                        row.classList.add('has-category');
                        row.style.borderLeftColor = task.category.color;
                        console.log('  Category:', task.category.name);
                    }
                    
                    // Будуємо HTML
                    let categoryHTML = '';
                    if (task.category) {
                        categoryHTML = `<span class="panel-task-category">${task.category.icon}</span>`;
                    }
                    
                    let timeHTML = '';
                    if (task.time) {
                        timeHTML = `<div class="panel-task-time">⏰ ${task.time}</div>`;
                    }
                    
                    row.innerHTML = `
                        <div class="left">
                            <input type="checkbox" class="panel-task-checkbox" data-id="${task._id}" ${task.is_completed ? 'checked' : ''}/>
                            ${categoryHTML}
                            <div class="panel-task-info">
                                <div class="panel-task-title">${escapeHtml(task.title)}</div>
                                ${timeHTML}
                            </div>
                        </div>
                        <div class="panel-task-actions">
                            <button class="edit-task-btn" data-id="${task._id}" title="Редагувати">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                                </svg>
                            </button>
                            <button class="delete-task-btn-inline" data-id="${task._id}" title="Видалити">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="3 6 5 6 21 6"/>
                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                                </svg>
                            </button>
                        </div>
                    `;
                    
                    // Додаємо обробники подій
                    try {
                        row.querySelector('.panel-task-checkbox').addEventListener('change', e => {
                            console.log('Toggle task:', task._id);
                            fetch(`/planner/toggle_task/${task._id}`, { method: 'POST' })
                                .then(r => r.json())
                                .then(() => { 
                                    loadTasks(date); 
                                    refreshCalendar(); 
                                })
                                .catch(err => console.error('Toggle error:', err));
                        });
                        
                        row.querySelector('.edit-task-btn').addEventListener('click', () => {
                            console.log('Edit task:', task._id);
                            openEditForm(task);
                        });
                        
                        row.querySelector('.delete-task-btn-inline').addEventListener('click', () => {
                            if(confirm('Видалити завдання?')) {
                                console.log('Delete task:', task._id);
                                fetch(`/planner/delete_task/${task._id}`, { method: 'POST' })
                                    .then(r => r.json())
                                    .then(res => {
                                        if(res.success || res.error === undefined) {
                                            loadTasks(date);
                                            refreshCalendar();
                                        } else {
                                            alert(res.error || 'Помилка видалення');
                                        }
                                    })
                                    .catch(err => {
                                        console.error('Delete error:', err);
                                        alert('Помилка видалення: ' + err.message);
                                    });
                            }
                        });
                    } catch(e) {
                        console.error('Error attaching event listeners:', e);
                    }
                    
                    list.appendChild(row);
                    console.log(`  ✅ Row ${index + 1} appended`);
                });
                
                console.log('=== LOAD_TASKS COMPLETED ===');
            })
            .catch(err => {
                console.error('=== FETCH ERROR ===');
                console.error('Error:', err);
                console.error('Stack:', err.stack);
                list.innerHTML = `<div class="empty" style="color: #ff6b6b;">❌ Помилка: ${err.message}</div>`;
            });
    }
    
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
    
    function qs(sel, root = document) {
        return root.querySelector(sel);
    }
    
    function showPanelFor(date) {
        console.log('showPanelFor called with date:', date);
        const panel = qs('#eventPanel');
        const calendarSection = qs('#calendarSection');
        
        if (!panel) {
            console.error('❌ eventPanel not found!');
            return;
        }
        
        qsa('.day-cell').forEach(el => el.classList.toggle('selected', el.dataset.date === date));
        
        const panelDate = qs('#panelDate');
        if (panelDate) {
            panelDate.textContent = formatDate(date);
        }
        
        panel.classList.remove('hidden');
        if (calendarSection) {
            calendarSection.classList.remove('full-width');
        }
        
        switchTab('tasks');
        resetForm();
        loadTasks(date);
    }
    
    function qsa(sel, root = document) {
        return Array.from(root.querySelectorAll(sel));
    }
    
    function formatDate(dateStr) {
        const date = new Date(dateStr + 'T00:00:00');
        const days = ['Неділя', 'Понеділок', 'Вівторок', 'Середа', 'Четвер', 'П\'ятниця', 'Субота'];
        const months = ['січня', 'лютого', 'березня', 'квітня', 'травня', 'червня', 
                        'липня', 'серпня', 'вересня', 'жовтня', 'листопада', 'грудня'];
        return `${days[date.getDay()]}, ${date.getDate()} ${months[date.getMonth()]}`;
    }
    
    function switchTab(tabName) {
        qsa('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        qsa('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === 'tab' + tabName.charAt(0).toUpperCase() + tabName.slice(1));
        });
    }
    
    function resetForm() {
        const form = qs('#taskForm');
        if (form) form.reset();
        const taskId = qs('#taskId');
        if (taskId) taskId.value = '';
        const deleteBtn = qs('#deleteTaskBtn');
        if (deleteBtn) deleteBtn.style.display = 'none';
    }
    
    function openEditForm(task) {
        console.log('Opening edit form for task:', task);
        switchTab('create');
        qs('#taskId').value = task._id;
        qs('#taskTitle').value = task.title;
        qs('#taskDescription').value = task.description || '';
        qs('#taskTime').value = task.time || '';
        qs('#deleteTaskBtn').style.display = 'inline-flex';
        qs('#taskTitle').focus();
    }
    
    function refreshCalendar() {
        console.log('Refreshing calendar...');
        // Можеш замінити на AJAX замість повного перезавантаження
        // location.reload();
    }
})
