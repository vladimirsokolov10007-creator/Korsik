const state = {
  userId: "demo-employee-alina",
  stage: "idle",
  sending: false,
  currentRole: "employee",
};

const roleChoices = [
  { label: "Инженер-технолог", value: "Инженер-технолог" },
  { label: "Специалист по клиентам", value: "Специалист по работе с клиентами" },
  { label: "Аналитик", value: "Аналитик" },
  { label: "Другая должность", action: "custom-role" },
];

const stageSuggestions = {
  idle: [
    { label: "Начать", action: "start", primary: true },
    { label: "Рабочий график", question: "Какой рабочий график?" },
    { label: "Подготовить обращение HR", question: "/hr" },
  ],
  job: roleChoices,
  experience: [
    { label: "Нет опыта", value: "нет опыта" },
    { label: "Есть опыт", value: "есть опыт" },
  ],
  location: [
    { label: "GrPP", value: "GrPP" },
    { label: "GTP", value: "GTP" },
    { label: "Luzhniki", value: "Luzhniki" },
    { label: "Пока не знаю", value: "не знаю" },
  ],
  hrMessage: [{ label: "Отменить", question: "/cancel" }],
  hrConfirm: [
    { label: "Отправить HR", question: "Отправить HR", primary: true },
    { label: "Изменить текст", question: "Изменить текст" },
    { label: "Не сейчас", question: "Не сейчас" },
  ],
  reminders: [
    { label: "Получать напоминания", question: "получать", primary: true },
    { label: "Не получать", question: "не получать" },
  ],
  ready: [
    { label: "Мой маршрут", question: "/status" },
    { label: "Рабочий график", question: "Какой рабочий график?" },
    { label: "Что в первый день?", question: "Что происходит в первый день?" },
    { label: "Подготовить обращение HR", question: "/hr" },
  ],
};

const serverStageMap = {
  ask_job: "job",
  ask_experience: "experience",
  ask_location: "location",
  ask_start_date: "date",
  ask_reminders: "reminders",
  hr_ask_message: "hrMessage",
  hr_confirm: "hrConfirm",
  ready: "ready",
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Ошибка сервера: ${response.status}`);
  }
  return response.json();
}

function timeNow() {
  return new Intl.DateTimeFormat("ru-RU", { hour: "2-digit", minute: "2-digit" }).format(new Date());
}

function escapeHtml(value) {
  return String(value).replace(/[&<>\"]/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[char]));
}

function scrollToBottom() {
  const log = document.querySelector("#chat-log");
  requestAnimationFrame(() => { log.scrollTop = log.scrollHeight; });
}

function setConversationPreview(text) {
  const compact = String(text).replace(/\s+/g, " ").trim();
  document.querySelector("#conversation-preview").textContent = compact.slice(0, 52) || "AI-наставник по адаптации";
}

function addMessage(kind, text, sources = []) {
  const fragment = document.querySelector("#message-template").content.cloneNode(true);
  const article = fragment.querySelector(".message");
  article.classList.add(kind);
  fragment.querySelector(".message-text").textContent = text;
  fragment.querySelector("time").textContent = timeNow();

  if (sources.length) {
    const sourcesBox = fragment.querySelector(".sources");
    sources.forEach(source => {
      const line = document.createElement("div");
      line.textContent = `Источник: ${source.document} — ${source.section}`;
      sourcesBox.append(line);
    });
  }

  document.querySelector("#chat-log").append(fragment);
  setConversationPreview(kind === "bot" ? text : `Вы: ${text}`);
  scrollToBottom();
}

function localDate(dayOffset) {
  const date = new Date();
  date.setDate(date.getDate() + dayOffset);
  return `${String(date.getDate()).padStart(2, "0")}.${String(date.getMonth() + 1).padStart(2, "0")}.${date.getFullYear()}`;
}

function applyDialogState(dialogState) {
  state.stage = serverStageMap[dialogState] || "ready";
  updateSuggestions();
}

function updateSuggestions() {
  const panel = document.querySelector("#suggestion-panel");
  const field = document.querySelector("#chat-text");
  let options = stageSuggestions[state.stage] || stageSuggestions.ready;

  if (state.stage === "date") {
    const mondayOffset = (8 - new Date().getDay()) % 7 || 7;
    options = [
      { label: `Завтра, ${localDate(1)}`, value: localDate(1) },
      { label: `В понедельник, ${localDate(mondayOffset)}`, value: localDate(mondayOffset) },
    ];
    field.placeholder = "Введите дату: ДД.ММ.ГГГГ";
  } else if (state.stage === "job") {
    field.placeholder = "Напишите должность…";
  } else if (state.stage === "hrMessage") {
    field.placeholder = "Опишите вопрос для HR…";
  } else {
    field.placeholder = "Написать сообщение…";
  }

  panel.innerHTML = "";
  options.forEach(option => {
    const button = document.createElement("button");
    button.className = `suggestion${option.primary ? " primary-suggestion" : ""}`;
    button.type = "button";
    button.textContent = option.label;
    if (option.action) button.dataset.action = option.action;
    if (option.value) button.dataset.value = option.value;
    if (option.question) button.dataset.question = option.question;
    panel.append(button);
  });
}

function setSending(isSending) {
  state.sending = isSending;
  const send = document.querySelector(".send");
  send.disabled = isSending;
  send.textContent = isSending ? "…" : "➤";
}

function offlineResult(text) {
  const normalised = text.trim().toLowerCase();
  if (normalised === "/start") {
    return { text: "Отлично! Соберём персональный маршрут. Какая у вас должность?", dialog_state: "ask_job" };
  }
  if (normalised === "/hr") {
    return { text: "Опишите вопрос одним сообщением. Перед отправкой я покажу текст обращения и попрошу подтвердить передачу HR.", dialog_state: "hr_ask_message" };
  }
  if (normalised === "/cancel") {
    return { text: "В автономном демо опрос остановлен. При подключённом сервисе команда также отменяет будущие напоминания.", dialog_state: "ready" };
  }
  if (normalised === "/status") {
    return {
      text: "Маршрут адаптации: до первого дня уточните время и место выхода у руководителя или HR; в первый день познакомьтесь с командой, уточните первые задачи, нужные доступы и оборудование.",
      dialog_state: "ready",
    };
  }
  if (state.stage === "job") {
    return { text: "Спасибо. Есть ли у вас опыт на похожей должности? Выберите «есть опыт» или «нет опыта».", dialog_state: "ask_experience" };
  }
  if (state.stage === "experience") {
    return { text: "На какой площадке вы будете работать? Выберите GrPP, GTP или Luzhniki. Если пока не знаете, напишите «не знаю».", dialog_state: "ask_location" };
  }
  if (state.stage === "location") {
    return { text: "Когда ваш первый рабочий день? Введите дату в формате ДД.ММ.ГГГГ.", dialog_state: "ask_start_date" };
  }
  if (state.stage === "date") {
    return {
      text: "Маршрут готов.\n\n• До первого дня: уточните время и место выхода у руководителя или HR. Если вам выдали список документов, проверьте его; не отправляйте документы в чат.\n• В первый день: познакомьтесь с руководителем и командой, уточните первые задачи, нужные доступы и оборудование.\n\nХотите получать короткие напоминания о ходе адаптации?",
      dialog_state: "ask_reminders",
    };
  }
  if (state.stage === "reminders") {
    const enabled = ["получать", "да", "хочу", "включить"].includes(normalised);
    return {
      text: enabled
        ? "В автономном демо напоминания не отправляются. При подключённом сервисе они будут включены только после вашего согласия; отключить их можно командой /cancel."
        : "Напоминания не включены. Маршрут остаётся доступен по команде /status.",
      dialog_state: "ready",
    };
  }
  if (state.stage === "hrMessage") {
    if (text.trim().length < 5) return { text: "Опишите вопрос немного подробнее или нажмите «Отменить».", dialog_state: "hr_ask_message" };
    return {
      text: `Проверьте текст обращения:\n«${text.trim()}»\n\nНажмите «Отправить HR», чтобы подтвердить передачу, «Изменить текст» или «Не сейчас».`,
      dialog_state: "hr_confirm",
    };
  }
  if (state.stage === "hrConfirm") {
    if (["отправить hr", "/sendhr", "отправить"].includes(normalised)) {
      return { text: "Автономное демо не передаёт сообщение HR. В подключённом сервисе обращение будет создано только после этого подтверждения.", dialog_state: "ready" };
    }
    if (["изменить текст", "изменить", "редактировать"].includes(normalised)) {
      return { text: "Напишите новую версию обращения. Я снова покажу её перед подтверждением.", dialog_state: "hr_ask_message" };
    }
    if (["не сейчас", "нет", "отмена"].includes(normalised)) {
      return { text: "Обращение не отправлено. Вернуться к нему можно командой /hr.", dialog_state: "ready" };
    }
    return { text: "Чтобы подтвердить передачу, нажмите «Отправить HR». Также можно выбрать «Изменить текст» или «Не сейчас».", dialog_state: "hr_confirm" };
  }
  if (normalised.includes("график")) {
    return { text: "Рабочий график определяется правилами подразделения и руководителем. В первый рабочий день уточните время выхода и формат работы у руководителя.", dialog_state: "ready" };
  }
  if (normalised.includes("первый день")) {
    return { text: "В первый день познакомьтесь с руководителем и командой, уточните первые задачи, а также какие доступы или оборудование понадобятся для работы.", dialog_state: "ready" };
  }
  return {
    text: `В автономном демо нет доступа к корпоративной базе знаний. Я не буду придумывать ответ. Могу показать, как подготовить обращение HR с вашим текстом:\n«${text.trim()}»\n\nДля продолжения нажмите «Отправить HR», «Изменить текст» или «Не сейчас».`,
    dialog_state: "hr_confirm",
  };
}

async function sendQuestion(rawText) {
  const text = rawText.trim();
  if (!text || state.sending) return;

  addMessage("user", text);
  setSending(true);
  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ user_id: state.userId, text }),
    });
    addMessage("bot", data.text, data.sources || []);
    applyDialogState(data.dialog_state);
  } catch (error) {
    if (window.location.protocol === "file:") {
      document.querySelector("#service-status").textContent = "Автономное демо — без отправки данных";
      const data = offlineResult(text);
      addMessage("bot", data.text);
      applyDialogState(data.dialog_state);
    } else {
      addMessage("bot", `Не удалось отправить сообщение: ${error.message}. Проверьте соединение и повторите попытку.`);
    }
  } finally {
    setSending(false);
  }
}

const roleMeta = {
  employee: { title: "Корсик", subtitle: "AI-наставник по адаптации" },
  hr: { title: "Корсик для HR", subtitle: "Подтверждённые обращения и агрегированные сигналы" },
  manager: { title: "Корсик для руководителя", subtitle: "Статусы команды в адаптации" },
  director: { title: "Корсик: дайджест", subtitle: "Агрегированная аналитика адаптации" },
};

const mockRoleData = {
  hr: {
    summary: { employees: 3, open_escalations: 1, feedback_total: 3, risk_feedback: 1 },
    escalations: [{ id: 1, display_name: "София Лебедева", job_title: "Аналитик", reason: "Обращение подтверждено сотрудником", source_message: "Много задач, не успеваю и нет обратной связи." }],
    analytics: { topics: { адаптация: 2, доступы: 1, нагрузка: 1 } },
  },
  manager: {
    team: [
      { display_name: "Алина Воронцова", job_title: "Специалист по работе с клиентами", onboarding_stage: "маршрут готов", location: "GrPP" },
      { display_name: "София Лебедева", job_title: "Аналитик", onboarding_stage: "нужен check-in", location: "Luzhniki" },
    ],
    meeting_prompt: "Запланируйте личную встречу с каждым новым сотрудником в первую неделю.",
  },
  director: {
    weekly_digest: { sample_size: 3, sentiment: { positive: 1, negative: 1 }, risk_feedback: 1, top_topics: [{ topic: "адаптация", count: 2 }, { topic: "доступы", count: 1 }, { topic: "нагрузка", count: 1 }] },
    note: "Демонстрационная сводка: в подключённой версии период должен задаваться в отчёте. Используются только агрегированные данные — без личных диалогов сотрудников.",
  },
};

function showRoleChrome(role) {
  const meta = roleMeta[role];
  document.querySelector("#role-title").textContent = meta.title;
  document.querySelector("#role-subtitle").innerHTML = `<span class="online-dot"></span>${meta.subtitle}`;
  document.querySelectorAll(".role-tab").forEach(tab => tab.classList.toggle("active", tab.dataset.role === role));
}

function cleanStage(value) {
  return String(value || "—").replaceAll("_", " ");
}

async function getRoleData(role) {
  if (window.location.protocol === "file:") {
    document.querySelector("#service-status").textContent = "Автономное демо — без отправки данных";
    return { data: mockRoleData[role], demo: true };
  }
  try {
    const endpoint = role === "hr" ? "/api/dashboard/hr" : `/api/dashboard/${role}`;
    return { data: await api(endpoint), demo: false };
  } catch {
    return { data: mockRoleData[role], demo: true };
  }
}

function renderRoleIntro(role, data, demo) {
  const log = document.querySelector("#chat-log");
  const card = document.createElement("section");
  card.className = "role-feed";
  const demoBadge = demo ? '<p class="demo-badge">Демонстрационные данные: действия не отправляются</p>' : "";

  if (role === "hr") {
    const summary = data.summary;
    const escalation = data.escalations[0];
    card.innerHTML = `
      ${demoBadge}<h2>HR-менеджер</h2>
      <p>HR видит только обращения, которые сотрудник просмотрел и явно подтвердил к передаче, а также агрегированные сигналы.</p>
      <div class="data-flow"><div class="flow-step"><strong>Новый сотрудник</strong>Сам решает, передавать ли вопрос</div><div class="flow-arrow">→</div><div class="flow-step"><strong>Корсик</strong>Показывает текст для подтверждения</div><div class="flow-arrow">→</div><div class="flow-step"><strong>HR</strong>Получает подтверждённое обращение</div></div>
      <div class="role-metrics"><div class="role-metric"><strong>${escapeHtml(summary.employees)}</strong><span>сотрудников в адаптации</span></div><div class="role-metric"><strong>${escapeHtml(summary.open_escalations)}</strong><span>открытых обращений</span></div><div class="role-metric"><strong>${escapeHtml(summary.risk_feedback)}</strong><span>агрегированных сигналов</span></div></div>
      <div class="role-list"><div class="role-list-item"><strong>${escapeHtml(escalation?.display_name || "Нет открытых обращений")}</strong><span>${escapeHtml(escalation ? `${escalation.reason}: ${escalation.source_message}` : "Здесь появятся подтверждённые обращения.")}</span></div></div>
      <p class="role-privacy">Личная переписка сотрудника не становится HR-дашбордом: он видит только явно переданные обращения и агрегированные показатели.</p>`;
  }

  if (role === "manager") {
    const team = data.team || [];
    card.innerHTML = `
      ${demoBadge}<h2>Руководитель подразделения</h2>
      <p>Руководитель получает статус адаптации своих новых коллег без доступа к личному диалогу с ботом.</p>
      <div class="data-flow"><div class="flow-step"><strong>Новый сотрудник</strong>Проходит маршрут и check-in</div><div class="flow-arrow">→</div><div class="flow-step"><strong>Корсик</strong>Фиксирует этап адаптации</div><div class="flow-arrow">→</div><div class="flow-step"><strong>Руководитель</strong>Получает повод для личной встречи</div></div>
      <div class="role-list">${team.length ? team.map(member => `<div class="role-list-item"><strong>${escapeHtml(member.display_name)} · ${escapeHtml(member.job_title)}</strong><span>Этап: ${escapeHtml(cleanStage(member.onboarding_stage))} · Площадка: ${escapeHtml(member.location)}</span></div>`).join("") : '<div class="role-list-item"><strong>Пока нет сотрудников</strong><span>После заполнения маршрутов здесь появится команда в адаптации.</span></div>'}</div>
      <button class="role-action" type="button" data-manager-action="meeting">Показать напоминание о встрече</button>
      <p class="role-privacy">${escapeHtml(data.meeting_prompt)}</p>`;
  }

  if (role === "director") {
    const digest = data.weekly_digest;
    const topics = digest.top_topics || [];
    card.innerHTML = `
      ${demoBadge}<h2>Руководитель управления</h2>
      <p>Корсик формирует обезличенную сводку по выбранному периоду, чтобы улучшать процесс адаптации, а не оценивать конкретных сотрудников.</p>
      <div class="data-flow"><div class="flow-step"><strong>Сотрудники</strong>Добровольные check-in и обратная связь</div><div class="flow-arrow">→</div><div class="flow-step"><strong>Корсик</strong>Агрегирует темы и риски</div><div class="flow-arrow">→</div><div class="flow-step"><strong>Руководитель</strong>Получает периодический дайджест</div></div>
      <div class="role-metrics"><div class="role-metric"><strong>${escapeHtml(digest.sample_size)}</strong><span>ответов в сводке</span></div><div class="role-metric"><strong>${escapeHtml(digest.risk_feedback)}</strong><span>зон внимания</span></div><div class="role-metric"><strong>${escapeHtml(topics[0]?.topic || "—")}</strong><span>главная тема периода</span></div></div>
      <div class="role-list">${topics.length ? topics.map(topic => `<div class="role-list-item"><strong>${escapeHtml(topic.topic)}</strong><span>${escapeHtml(topic.count)} упоминаний в агрегированной обратной связи</span></div>`).join("") : '<div class="role-list-item"><strong>Пока нет данных</strong><span>Сводка появится после добровольных ответов сотрудников.</span></div>'}</div>
      <p class="role-privacy">${escapeHtml(data.note)}</p>`;
  }

  log.append(card);
  scrollToBottom();
}

async function changeRole(role) {
  if (state.sending) return;
  state.currentRole = role;
  showRoleChrome(role);
  const isEmployee = role === "employee";
  document.querySelector("#suggestion-panel").hidden = !isEmployee;
  document.querySelector("#chat-form").hidden = !isEmployee;

  if (isEmployee) {
    state.stage = "idle";
    createWelcome();
    updateSuggestions();
    setConversationPreview("AI-наставник по адаптации");
    return;
  }

  document.querySelector("#chat-log").innerHTML = '<div class="day-label">Демонстрация потоков данных</div>';
  setConversationPreview("Ролевой сценарий");
  const { data, demo } = await getRoleData(role);
  renderRoleIntro(role, data, demo);
}

function createWelcome() {
  const log = document.querySelector("#chat-log");
  log.innerHTML = `
    <div class="day-label">Сегодня</div>
    <article class="message bot welcome-message">
      <p>Здравствуйте, Алина!</p>
      <p>Я Корсик — ваш AI-наставник. Помогу подготовиться к выходу, найти ответ в утверждённых документах и подготовить обращение HR, если нужна помощь человека.</p>
      <p>Сначала соберём короткий маршрут адаптации.</p>
      <button class="start-card" id="start-button" type="button">
        <span class="start-card-icon">↗</span>
        <span><strong>Начать адаптацию</strong><small>Отвечу на 4 коротких вопроса</small></span>
      </button>
    </article>`;
  document.querySelector("#start-button").addEventListener("click", () => sendQuestion("/start"));
}

function resetChat() {
  if (state.sending) return;
  state.currentRole = "employee";
  state.stage = "idle";
  showRoleChrome("employee");
  document.querySelector("#suggestion-panel").hidden = false;
  document.querySelector("#chat-form").hidden = false;
  createWelcome();
  updateSuggestions();
  setConversationPreview("AI-наставник по адаптации");
  document.querySelector("#chat-text").focus();
}

function autoResize(field) {
  field.style.height = "auto";
  field.style.height = `${Math.min(field.scrollHeight, 120)}px`;
}

function handleSuggestion(event) {
  const button = event.target.closest(".suggestion");
  if (!button || state.sending) return;
  if (button.dataset.action === "start") {
    sendQuestion("/start");
    return;
  }
  if (button.dataset.action === "custom-role") {
    const field = document.querySelector("#chat-text");
    field.focus();
    field.placeholder = "Введите свою должность…";
    return;
  }
  sendQuestion(button.dataset.value || button.dataset.question || "");
}

async function checkHealth() {
  const indicator = document.querySelector("#service-status");
  try {
    const health = await api("/api/health");
    indicator.textContent = health.mode === "demo" ? "Демо-режим: данные тестовые" : "Бот подключён";
  } catch {
    indicator.textContent = window.location.protocol === "file:" ? "Автономное демо — без отправки данных" : "Сервис пока недоступен";
  }
}

function initDialog() {
  const dialog = document.querySelector("#about-dialog");
  document.querySelector("#about-button").addEventListener("click", () => dialog.showModal());
  document.querySelector("#close-dialog").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", event => {
    if (event.target === dialog) dialog.close();
  });
}

function init() {
  const form = document.querySelector("#chat-form");
  const field = document.querySelector("#chat-text");
  createWelcome();
  updateSuggestions();
  checkHealth();
  initDialog();

  form.addEventListener("submit", event => {
    event.preventDefault();
    const value = field.value;
    if (!value.trim()) return;
    field.value = "";
    autoResize(field);
    sendQuestion(value);
  });
  field.addEventListener("input", () => autoResize(field));
  document.querySelector("#suggestion-panel").addEventListener("click", handleSuggestion);
  document.querySelector("#restart-button").addEventListener("click", resetChat);
  document.querySelectorAll(".role-tab").forEach(tab => tab.addEventListener("click", () => changeRole(tab.dataset.role)));
  document.querySelector("#chat-log").addEventListener("click", event => {
    const button = event.target.closest("[data-manager-action='meeting']");
    if (!button) return;
    button.textContent = "В демо напоминание не отправляется";
    button.disabled = true;
  });
}

init();
