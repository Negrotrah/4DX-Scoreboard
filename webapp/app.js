// ============================================
// Telegram WebApp
// ============================================
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

// ============================================
// Конфигурация
// ============================================
const API_URL = './data.json';

// ============================================
// Локализация
// ============================================
const TRANSLATIONS = {
  ru: {
    title: '📊 ТАБЛО ЦЕЛЕЙ',
    week: 'Неделя',
    mainGoal: '🎯 Главная цель:',
    prevWeek: 'Прошлая неделя:',
    previous: 'Прошлая:',
    submitted: '✓ Сдано',
    pending: '⏳ Ожидание',
    flag: '🇷🇺',
    // Названия отделов
    departments: {
      'Отдел продаж': 'Отдел продаж',
      'Отдел маркетинга': 'Отдел маркетинга',
      'Отдел разработки': 'Отдел разработки',
      'Отдел поддержки': 'Отдел поддержки',
      'Отдел HR': 'Отдел HR',
      'Отдел финансов': 'Отдел финансов',
      'Отдел логистики': 'Отдел логистики',
      'Отдел закупок': 'Отдел закупок'
    },
    // Показатели
    indicators: {
      'Встречи': 'Встречи',
      'Лиды': 'Лиды',
      'Задачи': 'Задачи',
      'Тикеты': 'Тикеты',
      'Собеседования': 'Собеседования',
      'Отчеты': 'Отчеты',
      'Доставки': 'Доставки',
      'Контракты': 'Контракты',
      'Сделки': 'Сделки',
      'Конверсии': 'Конверсии',
      'Релизы': 'Релизы',
      'NPS': 'NPS',
      'Наймы': 'Наймы',
      'Аудиты': 'Аудиты',
      'Оптимизации': 'Оптимизации',
      'Экономия': 'Экономия'
    }
  },
  en: {
    title: '📊 SCOREBOARD',
    week: 'Week',
    mainGoal: '🎯 Main goal:',
    prevWeek: 'Previous week:',
    previous: 'Previous:',
    submitted: '✓ Done',
    pending: '⏳ Pending',
    flag: '🇬🇧',
    // Department names
    departments: {
      'Отдел продаж': 'Sales',
      'Отдел маркетинга': 'Marketing',
      'Отдел разработки': 'Development',
      'Отдел поддержки': 'Support',
      'Отдел HR': 'HR',
      'Отдел финансов': 'Finance',
      'Отдел логистики': 'Logistics',
      'Отдел закупок': 'Procurement'
    },
    // Indicators
    indicators: {
      'Встречи': 'Meetings',
      'Лиды': 'Leads',
      'Задачи': 'Tasks',
      'Тикеты': 'Tickets',
      'Собеседования': 'Interviews',
      'Отчеты': 'Reports',
      'Доставки': 'Deliveries',
      'Контракты': 'Contracts',
      'Сделки': 'Deals',
      'Конверсии': 'Conversions',
      'Релизы': 'Releases',
      'NPS': 'NPS',
      'Наймы': 'Hires',
      'Аудиты': 'Audits',
      'Оптимизации': 'Optimizations',
      'Экономия': 'Savings'
    }
  }
};

let currentLang = 'ru';
let cachedData = null;
let langDirection = 1; // 1 = влево, -1 = вправо

function getStoredLang() {
  return localStorage.getItem('lang') || 'ru';
}

function setLang(lang, animate = false) {
  const btn = document.getElementById('langBtn');
  const newFlag = TRANSLATIONS[lang].flag;
  
  if (animate && btn.querySelector('span')) {
    // Направление: 1 = улетает влево, появляется справа
    //             -1 = улетает вправо, появляется слева
    const exitX = langDirection * -30;
    const enterX = langDirection * 30;
    
    // Анимация выхода
    const span = btn.querySelector('span');
    span.style.transform = `translateX(${exitX}px) rotate(${exitX * 0.7}deg)`;
    span.style.opacity = '0';
    
    // Плавно скрываем текст
    fadeOutTexts();
    
    setTimeout(() => {
      btn.innerHTML = `<span style="transform: translateX(${enterX}px) rotate(${enterX * 0.7}deg); opacity: 0;">${newFlag}</span>`;
      
      currentLang = lang;
      localStorage.setItem('lang', lang);
      
      // Меняем направление для следующего раза
      langDirection *= -1;
      
      // Обновляем только текст, не пересоздаём карточки
      updateAllTexts();
      
      requestAnimationFrame(() => {
        const newSpan = btn.querySelector('span');
        newSpan.style.transition = 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.4s ease';
        requestAnimationFrame(() => {
          newSpan.style.transform = 'translateX(0) rotate(0deg)';
          newSpan.style.opacity = '1';
          
          // Плавно показываем текст
          fadeInTexts();
        });
      });
    }, 300);
  } else {
    btn.innerHTML = `<span>${newFlag}</span>`;
    currentLang = lang;
    localStorage.setItem('lang', lang);
  }
}

function fadeOutTexts() {
  document.querySelectorAll('.header__title, .header__week, .main-goal__title, .main-goal__current, .main-goal__previous, .dept-card__name, .dept-card__status, .indicator__name, .indicator__value, .indicator__previous').forEach(el => {
    el.style.opacity = '0';
  });
}

function fadeInTexts() {
  document.querySelectorAll('.header__title, .header__week, .main-goal__title, .main-goal__current, .main-goal__previous, .dept-card__name, .dept-card__status, .indicator__name, .indicator__value, .indicator__previous').forEach(el => {
    el.style.opacity = '1';
  });
}

function updateAllTexts() {
  if (!cachedData) return;
  
  // Заголовок
  document.querySelector('.header__title').textContent = t('title');
  document.getElementById('weekLabel').textContent = `${t('week')} ${cachedData.week}, ${cachedData.year}`;
  
  // Главная цель
  const mainGoal = cachedData.mainGoal;
  document.querySelector('.main-goal__title').innerHTML = `${t('mainGoal')} <span id="goalTarget">${formatMoney(mainGoal.target)}</span>`;
  document.getElementById('mainPreviousText').textContent = 
    `${t('prevWeek')} ${formatMoney(mainGoal.previous)} (${formatPercent(mainGoal.previous, mainGoal.target)})`;
  
  // Карточки отделов — обновляем текст внутри существующих
  const cards = document.querySelectorAll('.dept-card');
  cachedData.departments.forEach((dept, index) => {
    if (cards[index]) {
      const card = cards[index];
      card.querySelector('.dept-card__name').textContent = tDept(dept.name);
      card.querySelector('.dept-card__status').textContent = dept.submitted ? t('submitted') : t('pending');
      
      const indicators = card.querySelectorAll('.indicator');
      // Опережающий показатель
      if (indicators[0]) {
        indicators[0].querySelector('.indicator__name').textContent = `📈 ${tIndicator(dept.leadIndicator.name)}`;
        indicators[0].querySelector('.indicator__previous').textContent = 
          `${t('previous')} ${formatNumber(dept.leadIndicator.previous)} (${formatPercent(dept.leadIndicator.previous, dept.leadIndicator.plan)})`;
      }
      // КВЦ
      if (indicators[1]) {
        indicators[1].querySelector('.indicator__name').textContent = `🎯 ${tIndicator(dept.kvts.name)}`;
        indicators[1].querySelector('.indicator__previous').textContent = 
          `${t('previous')} ${formatNumber(dept.kvts.previous)} (${formatPercent(dept.kvts.previous, dept.kvts.target)})`;
      }
    }
  });
}

function toggleLang() {
  setLang(currentLang === 'ru' ? 'en' : 'ru', true);
}

function t(key) {
  return TRANSLATIONS[currentLang][key] || key;
}

function tDept(name) {
  return TRANSLATIONS[currentLang].departments[name] || name;
}

function tIndicator(name) {
  return TRANSLATIONS[currentLang].indicators[name] || name;
}

function updateTexts() {
  // Не используется больше, рендерим заново
}

// ============================================
// Тема
// ============================================
function getStoredTheme() {
  return localStorage.getItem('theme') || 'dark';
}

function setTheme(theme, animate = false) {
  const btn = document.getElementById('themeBtn');
  const newIcon = theme === 'dark' ? '🌙' : '☀️';
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
  
  if (animate && btn.querySelector('span')) {
    // Луна уходит вниз → солнце появляется сверху
    // Солнце уходит вверх → луна появляется снизу
    const goingToLight = currentTheme === 'dark'; // переключаемся на светлую
    
    const exitY = goingToLight ? 30 : -30;   // луна вниз, солнце вверх
    const enterY = goingToLight ? -30 : 30;  // солнце сверху, луна снизу
    
    // Анимация выхода
    const span = btn.querySelector('span');
    span.style.transform = `translateY(${exitY}px) rotate(${exitY * 3}deg)`;
    span.style.opacity = '0';
    
    setTimeout(() => {
      btn.innerHTML = `<span style="transform: translateY(${enterY}px) rotate(${enterY * 3}deg); opacity: 0;">${newIcon}</span>`;
      
      // Анимация входа
      requestAnimationFrame(() => {
        const newSpan = btn.querySelector('span');
        newSpan.style.transition = 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.4s ease';
        requestAnimationFrame(() => {
          newSpan.style.transform = 'translateY(0) rotate(0deg)';
          newSpan.style.opacity = '1';
        });
      });
    }, 250);
  } else {
    btn.innerHTML = `<span>${newIcon}</span>`;
  }
  
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  setTheme(current === 'dark' ? 'light' : 'dark', true);
}

// ============================================
// Звёзды на фоне
// ============================================
function createStars() {
  const container = document.getElementById('stars');
  container.innerHTML = '';
  
  const count = 80;
  for (let i = 0; i < count; i++) {
    const star = document.createElement('div');
    star.className = 'star';
    
    const size = Math.random() * 2 + 1;
    star.style.width = size + 'px';
    star.style.height = size + 'px';
    star.style.left = Math.random() * 100 + '%';
    star.style.top = Math.random() * 100 + '%';
    star.style.opacity = Math.random() * 0.7 + 0.3;
    
    container.appendChild(star);
  }
}

// ============================================
// Форматирование
// ============================================
function formatMoney(value) {
  return '$' + value.toLocaleString('en-US');
}

function formatNumber(value) {
  return value.toLocaleString('ru-RU');
}

function formatPercent(value, target) {
  if (target === 0) return '0%';
  return Math.round((value / target) * 100) + '%';
}

function clampPercent(value, target) {
  if (target === 0) return 0;
  return Math.min(100, Math.max(0, (value / target) * 100));
}


// ============================================
// Рендер главной цели
// ============================================
function renderMainGoal(data) {
  const { target, current, previous } = data.mainGoal;
  
  document.querySelector('.header__title').textContent = t('title');
  document.getElementById('goalTarget').textContent = formatMoney(target);
  document.getElementById('weekLabel').textContent = `${t('week')} ${data.week}, ${data.year}`;
  
  // Проценты
  const currentPercent = clampPercent(current, target);
  const previousPercent = clampPercent(previous, target);
  
  // Анимация заполнения (с задержкой)
  setTimeout(() => {
    document.getElementById('mainCurrent').style.width = currentPercent + '%';
    document.getElementById('mainPrevious').style.width = previousPercent + '%';
  }, 100);
  
  // Текст
  document.getElementById('mainCurrentText').textContent = 
    `${formatMoney(current)} (${formatPercent(current, target)})`;
  document.getElementById('mainPreviousText').textContent = 
    `${t('prevWeek')} ${formatMoney(previous)} (${formatPercent(previous, target)})`;
}

// ============================================
// Рендер карточки отдела
// ============================================
function createDepartmentCard(dept, index) {
  const card = document.createElement('div');
  card.className = 'dept-card';
  
  // Проценты для шкал
  const leadCurrentPct = clampPercent(dept.leadIndicator.current, dept.leadIndicator.plan);
  const leadPrevPct = clampPercent(dept.leadIndicator.previous, dept.leadIndicator.plan);
  const kvtsCurrentPct = clampPercent(dept.kvts.current, dept.kvts.target);
  const kvtsPrevPct = clampPercent(dept.kvts.previous, dept.kvts.target);
  
  card.innerHTML = `
    <div class="dept-card__header">
      <span class="dept-card__name">${tDept(dept.name)}</span>
      <span class="dept-card__status ${dept.submitted ? '' : 'dept-card__status--pending'}">
        ${dept.submitted ? t('submitted') : t('pending')}
      </span>
    </div>
    
    <!-- Опережающий показатель -->
    <div class="indicator">
      <div class="indicator__header">
        <span class="indicator__name">📈 ${tIndicator(dept.leadIndicator.name)}</span>
        <span class="indicator__value">${formatNumber(dept.leadIndicator.current)} / ${formatNumber(dept.leadIndicator.plan)}</span>
      </div>
      <div class="indicator__bar">
        <div class="indicator__progress indicator__progress--previous" data-width="${leadPrevPct}"></div>
        <div class="indicator__progress indicator__progress--current" data-width="${leadCurrentPct}"></div>
      </div>
      <div class="indicator__previous">${t('previous')} ${formatNumber(dept.leadIndicator.previous)} (${formatPercent(dept.leadIndicator.previous, dept.leadIndicator.plan)})</div>
    </div>
    
    <!-- КВЦ -->
    <div class="indicator indicator--kvts">
      <div class="indicator__header">
        <span class="indicator__name">🎯 ${tIndicator(dept.kvts.name)}</span>
        <span class="indicator__value">${formatNumber(dept.kvts.current)} / ${formatNumber(dept.kvts.target)}</span>
      </div>
      <div class="indicator__bar">
        <div class="indicator__progress indicator__progress--previous" data-width="${kvtsPrevPct}"></div>
        <div class="indicator__progress indicator__progress--current" data-width="${kvtsCurrentPct}"></div>
      </div>
      <div class="indicator__previous">${t('previous')} ${formatNumber(dept.kvts.previous)} (${formatPercent(dept.kvts.previous, dept.kvts.target)})</div>
    </div>
  `;
  
  return card;
}

// ============================================
// Рендер всех отделов
// ============================================
function renderDepartments(departments) {
  const container = document.getElementById('departments');
  container.innerHTML = '';
  
  departments.forEach((dept, index) => {
    const card = createDepartmentCard(dept, index);
    container.appendChild(card);
    
    // Анимация появления карточки
    setTimeout(() => {
      card.classList.add('visible');
      
      // Анимация прогресс-баров после появления карточки
      setTimeout(() => {
        card.querySelectorAll('.indicator__progress').forEach(bar => {
          bar.style.width = bar.dataset.width + '%';
        });
      }, 200);
    }, index * 80);
  });
}


// ============================================
// Загрузка данных
// ============================================
async function fetchData() {
  try {
    const response = await fetch(API_URL + '?t=' + Date.now()); // cache bust
    if (!response.ok) throw new Error('API недоступен');
    return await response.json();
  } catch (error) {
    console.warn('Ошибка загрузки:', error.message);
    return null;
  }
}

// ============================================
// Обновление данных
// ============================================
async function refreshData(showAnimation = true) {
  const refreshBtn = document.getElementById('refreshBtn');
  
  if (showAnimation) {
    refreshBtn.classList.add('spinning');
  }
  
  const data = await fetchData();
  
  if (data) {
    cachedData = data; // Кэшируем для смены языка
    
    // Сбрасываем прогресс-бары перед обновлением
    document.querySelectorAll('.progress-bar, .indicator__progress').forEach(bar => {
      bar.style.width = '0%';
    });
    
    setTimeout(() => {
      renderMainGoal(data);
      renderDepartments(data.departments);
    }, 100);
  }
  
  if (showAnimation) {
    setTimeout(() => {
      refreshBtn.classList.remove('spinning');
    }, 800);
  }
}

// ============================================
// Pull to Refresh
// ============================================
let pullStartY = 0;
let isPulling = false;

function setupPullToRefresh() {
  const indicator = document.getElementById('pullIndicator');
  
  document.addEventListener('touchstart', (e) => {
    if (window.scrollY === 0) {
      pullStartY = e.touches[0].clientY;
      isPulling = true;
    }
  }, { passive: true });
  
  document.addEventListener('touchmove', (e) => {
    if (!isPulling) return;
    
    const pullDistance = e.touches[0].clientY - pullStartY;
    
    if (pullDistance > 0 && pullDistance < 150) {
      indicator.style.top = (pullDistance - 50) + 'px';
      indicator.style.transform = `translateX(-50%) rotate(${pullDistance * 3}deg)`;
      
      if (pullDistance > 60) {
        indicator.classList.add('visible');
      }
    }
  }, { passive: true });
  
  document.addEventListener('touchend', async () => {
    if (!isPulling) return;
    isPulling = false;
    
    const indicator = document.getElementById('pullIndicator');
    
    if (indicator.classList.contains('visible')) {
      indicator.classList.add('loading');
      await refreshData(false);
      
      setTimeout(() => {
        indicator.classList.remove('visible', 'loading');
        indicator.style.top = '-50px';
        indicator.style.transform = 'translateX(-50%)';
      }, 500);
    } else {
      indicator.style.top = '-50px';
      indicator.style.transform = 'translateX(-50%)';
    }
  });
}

// ============================================
// Инициализация
// ============================================
async function init() {
  // Тема
  setTheme(getStoredTheme());
  
  // Язык
  currentLang = getStoredLang();
  setLang(currentLang, false);
  
  // Звёзды
  createStars();
  
  // Загрузка данных
  await refreshData(false);
  
  // Pull to refresh
  setupPullToRefresh();
  
  // Кнопки
  document.getElementById('themeBtn').addEventListener('click', toggleTheme);
  document.getElementById('refreshBtn').addEventListener('click', () => refreshData(true));
  document.getElementById('langBtn').addEventListener('click', toggleLang);
  
  // Telegram theme (если есть)
  if (tg?.themeParams?.bg_color) {
    // Определяем тему по цвету фона Telegram
    const bgColor = tg.themeParams.bg_color;
    const isLight = parseInt(bgColor.slice(1), 16) > 0x808080;
    setTheme(isLight ? 'light' : 'dark');
  }
}

// Запуск
document.addEventListener('DOMContentLoaded', init);
