// ==================== ІНІЦІАЛІЗАЦІЯ ====================
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    createParticles();
    initClock();
});

function initializeApp() {
    const dayModal = document.getElementById('dayModal');
    const modalBackdrop = createBackdrop();
    
    if (dayModal) {
        initModal(dayModal, modalBackdrop);
        initDayClicks(dayModal, modalBackdrop);
        initTaskManagement();
        initDragAndDrop();
        initStickers();
        initColorPicker();
    }
}

// ==================== BACKDROP ====================
function createBackdrop() {
    let backdrop = document.querySelector('.modal-backdrop');
    if (!backdrop) {
        backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop';
        document.body.appendChild(backdrop);
    }
    return backdrop;
}

// ==================== МОДАЛЬНЕ ВІКНО ====================
function initModal(modal, backdrop) {
    const closeBtn = modal.querySelector('.close');
    
    // Закриття модального вікна
    if (closeBtn) {
        closeBtn.addEventListener('click', () => closeModal(modal, backdrop));
    }
    
    backdrop.addEventListener('click', () => closeModal(modal, backdrop));
    
    // Закриття на ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModal(modal, backdrop);
        }
    });
}

function openModal(modal, backdrop, date) {
    modal.classList.add('active');
    backdrop.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    const modalDate = document.getElementById('modalDate');
    if (modalDate) {
        modalDate.textContent = formatDate(date);
    }
    
    modal.dataset.currentDate = date;
    loadTasks(date);
    loadStickers(date);
}

function closeModal(modal, backdrop) {
    modal.classList.remove('active');
    backdrop.classList.remove('active');
    document.body.style.overflow = 'auto';
}

// ==================== КЛІКИ НА ДНІ ====================
function initDayClicks(modal, backdrop) {
    document.querySelectorAll('.day').forEach(day => {
        day.addEventListener('click', function(e) {
            if (!e.target.closest('button')) {
                const date = this.dataset.date;
                openModal(modal, backdrop, date);
            }
        });
        
        // Анімація при наведенні
        day.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.03)';
        });
        
        day.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

// ==================== ЗАДАЧІ ====================
function initTaskManagement() {
    const taskForm = document.querySelector('#dayModal form');
    
    if (taskForm) {
        taskForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(taskForm);
            const date = document.getElementById('dayModal').dataset.currentDate;
            
            formData.append('date', date);
            
            try {
                const response = await fetch('/planner/add_task', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    taskForm.reset();
                    loadTasks(date);
                    showNotification('Завдання додано!', 'success');
                    updateDayStatus(date);
                }
            } catch (error) {
                console.error('Помилка додавання завдання:', error);
                showNotification('Помилка додавання завдання', 'error');
            }
        });
    }
}

function createTaskElement(task) {
    const div = document.createElement('div');
    div.className = 'task-item';
    div.dataset.id = task._id || task.id;
    div.draggable = true;
    
    const isDone = task.is_completed ? 'done' : '';
    
    div.innerHTML = `
        <span class="${isDone}">${task.title || task.description}</span>
        <div style="display: flex; gap: 5px;">
            <button onclick="toggleTask('${task._id || task.id}')" title="Виконано">✓</button>
            <button onclick="deleteTask('${task._id || task.id}')" title="Видалити">🗑</button>
        </div>
    `;
    
    return div;
}

async function toggleTask(taskId) {
    try {
        const response = await fetch(`/planner/toggle_task/${taskId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const date = document.getElementById('dayModal').dataset.currentDate;
            loadTasks(date);
            showNotification('Статус оновлено!', 'success');
            updateDayStatus(date);
        }
    } catch (error) {
        console.error('Помилка зміни статусу:', error);
        showNotification('Помилка оновлення', 'error');
    }
}

async function deleteTask(taskId) {
    if (!confirm('Видалити це завдання?')) return;
    
    try {
        const response = await fetch(`/planner/delete_task/${taskId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const date = document.getElementById('dayModal').dataset.currentDate;
            loadTasks(date);
            showNotification('Завдання видалено!', 'success');
            updateDayStatus(date);
        }
    } catch (error) {
        console.error('Помилка видалення:', error);
        showNotification('Помилка видалення', 'error');
    }
}

// ==================== DRAG & DROP ====================
function initDragAndDrop() {
    initTaskDragging();
    initDayDropZones();
}

function initTaskDragging() {
    const tasks = document.querySelectorAll('.task-item');
    
    tasks.forEach(task => {
        task.addEventListener('dragstart', handleDragStart);
        task.addEventListener('dragend', handleDragEnd);
    });
}

function initDayDropZones() {
    const days = document.querySelectorAll('.day');
    
    days.forEach(day => {
        day.addEventListener('dragover', handleDragOver);
        day.addEventListener('drop', handleDrop);
        day.addEventListener('dragleave', handleDragLeave);
    });
}

let draggedTask = null;

function handleDragStart(e) {
    draggedTask = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
}

function handleDragEnd(e) {
    this.classList.remove('dragging');
}

function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    e.dataTransfer.dropEffect = 'move';
    this.style.boxShadow = '0 0 20px rgba(255, 123, 156, 0.6)';
    return false;
}

function handleDragLeave(e) {
    this.style.boxShadow = '';
}

async function handleDrop(e) {
    if (e.stopPropagation) {
        e.stopPropagation();
    }
    
    this.style.boxShadow = '';
    
    if (draggedTask) {
        const taskId = draggedTask.dataset.id;
        const newDate = this.dataset.date;
        
        try {
            const response = await fetch(`/planner/move_task/${taskId}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({new_date: newDate})
            });
            
            if (response.ok) {
                showNotification('Завдання переміщено!', 'success');
                setTimeout(() => location.reload(), 500);
            }
        } catch (error) {
            console.error('Помилка переміщення:', error);
            showNotification('Помилка переміщення', 'error');
        }
        
        draggedTask = null;
    }
    
    return false;
}

// ==================== СТІКЕРИ ====================
function initStickers() {
    const stickersContainer = document.getElementById('stickersContainer');
    if (!stickersContainer) return;
    
    const stickers = ['🎉', '⭐', '❤️', '🔥', '💪', '🎯', '✨', '🌟', '💖', '🎈', '🏆', '🎨', '📚', '☕', '🌈'];
    
    stickersContainer.innerHTML = '';
    stickers.forEach(sticker => {
        const stickerDiv = document.createElement('div');
        stickerDiv.className = 'sticker-item';
        stickerDiv.textContent = sticker;
        stickerDiv.addEventListener('click', () => addStickerToDay(sticker));
        stickersContainer.appendChild(stickerDiv);
    });
}

async function addStickerToDay(sticker) {
    const date = document.getElementById('dayModal').dataset.currentDate;
    
    try {
        const response = await fetch('/planner/add_sticker', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({date: date, sticker: sticker})
        });
        
        if (response.ok) {
            showNotification(`Стікер ${sticker} додано!`, 'success');
            loadStickers(date);
        }
    } catch (error) {
        console.error('Помилка додавання стікера:', error);
    }
}

async function loadStickers(date) {
    // Завантаження стікерів для конкретного дня
    try {
        const response = await fetch(`/planner/get_stickers/${date}`);
        const stickers = await response.json();
        
        // Відображення стікерів на дні календаря
        const dayElement = document.querySelector(`.day[data-date="${date}"]`);
        if (dayElement && stickers.length > 0) {
            const stickersDisplay = dayElement.querySelector('.day-stickers') || document.createElement('div');
            stickersDisplay.className = 'day-stickers';
            stickersDisplay.innerHTML = stickers.map(s => `<span>${s}</span>`).join('');
            if (!dayElement.querySelector('.day-stickers')) {
                dayElement.appendChild(stickersDisplay);
            }
        }
    } catch (error) {
        console.error('Помилка завантаження стікерів:', error);
    }
}

// ==================== ВИБІР КОЛЬОРУ ====================
function initColorPicker() {
    const colorInput = document.createElement('input');
    colorInput.type = 'color';
    colorInput.id = 'dayColor';
    colorInput.value = '#ff7b9c';
    colorInput.style.display = 'none';
    
    const colorBtn = document.createElement('button');
    colorBtn.className = 'btn';
    colorBtn.textContent = '🎨 Змінити колір дня';
    colorBtn.onclick = () => colorInput.click();
    
    const modal = document.getElementById('dayModal');
    if (modal) {
        const form = modal.querySelector('form');
        if (form) {
            form.appendChild(colorBtn);
            form.appendChild(colorInput);
            
            colorInput.addEventListener('change', async (e) => {
                const date = modal.dataset.currentDate;
                const color = e.target.value;
                
                try {
                    await fetch('/planner/set_day_color', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({date: date, color: color})
                    });
                    
                    const dayElement = document.querySelector(`.day[data-date="${date}"]`);
                    if (dayElement) {
                        dayElement.style.background = `linear-gradient(135deg, ${color}33, ${color}11)`;
                        dayElement.style.borderColor = color;
                    }
                    
                    showNotification('Колір дня змінено!', 'success');
                } catch (error) {
                    console.error('Помилка зміни кольору:', error);
                }
            });
        }
    }
}

// ==================== ОНОВЛЕННЯ СТАТУСУ ДНЯ ====================
async function updateDayStatus(date) {
    try {
        const response = await fetch(`/planner/get_tasks/${date}`);
        const tasks = await response.json();
        
        const dayElement = document.querySelector(`.day[data-date="${date}"]`);
        if (!dayElement) return;
        
        const allCompleted = tasks.length > 0 && tasks.every(t => t.is_completed);
        
        if (allCompleted) {
            dayElement.classList.add('completed');
        } else {
            dayElement.classList.remove('completed');
        }
    } catch (error) {
        console.error('Помилка оновлення статусу дня:', error);
    }
}

// ==================== ГОДИННИК ====================
function initClock() {
    const clockDiv = document.getElementById('clock');
    if (!clockDiv) return;
    
    function updateClock() {
        const now = new Date();
        const h = now.getHours().toString().padStart(2,'0');
        const m = now.getMinutes().toString().padStart(2,'0');
        const s = now.getSeconds().toString().padStart(2,'0');
        clockDiv.textContent = `${h}:${m}:${s}`;
    }
    
    updateClock();
    setInterval(updateClock, 1000);
}

// ==================== СПОВІЩЕННЯ ====================
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = 'notification glass';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === 'success' ? 'rgba(76, 217, 100, 0.9)' : type === 'error' ? 'rgba(255, 59, 48, 0.9)' : 'rgba(255, 123, 156, 0.9)'};
        color: white;
        border-radius: 12px;
        z-index: 3000;
        animation: slideInRight 0.3s ease, fadeOut 0.3s ease 2.7s;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// ==================== АНІМОВАНІ ЧАСТИНКИ ====================
function createParticles() {
    const particlesContainer = document.createElement('div');
    particlesContainer.className = 'particles';
    document.body.appendChild(particlesContainer);
    
    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 20 + 's';
        particle.style.animationDuration = (15 + Math.random() * 10) + 's';
        particlesContainer.appendChild(particle);
    }
}

// ==================== ДОПОМІЖНІ ФУНКЦІЇ ====================
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    return date.toLocaleDateString('uk-UA', options);
}

// // ==================== АНІМАЦІЇ ПРИ СКРОЛІ ====================
// window.addEventListener('scroll', () => {
//     const days = document.querySelectorAll('.day');
//     days.forEach((day, index) => {
//         const rect = day.getBoundingClientRect();
//         if (rect.top < window.innerHeight * 0.9) {
//             day.style.opacity = '1';
//             day.style.transform = 'translateY(0)';
//         }
//     });
// });
// document.addEventListener('DOMContentLoaded', () => {
//     const days = document.querySelectorAll('.day');
//     days.forEach((day, index) => {
//         setTimeout(() => {
//             day.classList.add('show');
//         }, index * 50);
//     });
// });
// days.forEach(day => {
//     day.addEventListener('click', () => {
//         const modal = document.getElementById('dayModal');
//         modal.style.display = 'block';
//         const date = day.dataset.date;
//         document.getElementById('modalDate').innerText = date;

//         // додаємо дату до форми, щоб додати таск
//         const taskForm = modal.querySelector('form');
//         let hiddenDateInput = taskForm.querySelector('input[name="date"]');
//         if (!hiddenDateInput) {
//             hiddenDateInput = document.createElement('input');
//             hiddenDateInput.type = 'hidden';
//             hiddenDateInput.name = 'date';
//             taskForm.appendChild(hiddenDateInput);
//         }
//         hiddenDateInput.value = date;

//         const finishBtn = document.getElementById('finishDayBtn');
//         finishBtn.href = `/planner/day_entry/${date}`;
//     });
// });

// ==================== ГЛОБАЛЬНІ ФУНКЦІЇ ====================
window.toggleTask = toggleTask;
window.deleteTask = deleteTask;