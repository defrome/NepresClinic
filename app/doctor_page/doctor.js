(() => {
  const API = "/api/v1";
  const state = { token: sessionStorage.getItem("nepres_doctor_token"), user: null, view: "overview", patients: [], plans: [], templates: [], currentPatient: null };
  const $ = (selector) => document.querySelector(selector);
  const icon = () => window.lucide?.createIcons({ attrs: { "stroke-width": 1.75 } });
  const escape = (value) => String(value ?? "—").replace(/[&<>'"]/g, (character) => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", "'":"&#39;", '"':"&quot;" }[character]));
  async function request(path, options = {}) {
    const response = await fetch(`${API}${path}`, { ...options, headers: { "Content-Type": "application/json", Authorization: `Bearer ${state.token}`, ...(options.headers || {}) } });
    if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail || "Не удалось выполнить запрос"); }
    return response.status === 204 ? null : response.json();
  }
  function setScreen(authenticated) { $("#login-screen").classList.toggle("is-hidden", authenticated); $("#doctor-app").classList.toggle("is-hidden", !authenticated); icon(); }
  function empty(title, text, iconName) { return `<section class="panel"><div class="empty-state"><i data-lucide="${iconName}"></i><h2>${title}</h2><p>${text}</p></div></section>`; }
  function loading() { $("#page-content").innerHTML = `<section class="panel"><div class="loading-state"><i data-lucide="loader-circle"></i><h2>Загружаем данные</h2><p>Пожалуйста, подождите.</p></div></section>`; icon(); }
  function renderOverview() {
    const total = state.patients.length;
    $("#page-content").innerHTML = `<section class="overview"><div class="stats-grid"><article class="stat-card"><span class="stat-label">Мои пациенты</span><strong class="stat-value">${total}</strong></article><article class="stat-card"><span class="stat-label">Активные планы</span><strong class="stat-value">${state.plans.filter((plan) => plan.status === "active").length}</strong></article><article class="stat-card"><span class="stat-label">Все планы лечения</span><strong class="stat-value">${state.plans.length}</strong></article></div>${empty("Рабочее пространство готово", total ? "Откройте список пациентов, чтобы продолжить работу с их карточками." : "Создайте первую карточку пациента. После этого можно будет назначить ему цифровой маршрут лечения.", "clipboard-plus")}</section>`;
    icon();
  }
  function renderPatients() {
    const query = $("#search-input").value.trim().toLowerCase();
    const visible = state.patients.filter((patient) => `${patient.first_name} ${patient.last_name} ${patient.phone || ""} ${patient.email || ""}`.toLowerCase().includes(query));
    const row = (patient) => `<button class="table-row patient-row" type="button" data-patient-id="${patient.id}" aria-label="Открыть подробности: ${escape(patient.full_name)}"><span class="table-cell is-wide" title="${escape(patient.full_name)}">${escape(patient.full_name)}</span><span class="table-cell">${escape(patient.sex === "male" ? "Мужской" : patient.sex === "female" ? "Женский" : "Не указан")}</span><span class="table-cell">${escape(patient.phone || patient.email)}</span><span class="table-cell" title="${escape(patient.diagnosis)}" aria-label="Диагноз: ${escape(patient.diagnosis)}">${escape(patient.diagnosis)}</span></button>`;
    $("#page-content").innerHTML = `<section class="patients-view"><section class="panel"><div class="panel-heading"><h2>Мои пациенты</h2><p>${visible.length} из ${state.patients.length}</p></div>${visible.length ? `<div class="table"><div class="table-row table-head"><div class="table-cell is-wide">Пациент</div><div class="table-cell">Пол</div><div class="table-cell">Контакт</div><div class="table-cell">Диагноз / повод</div></div>${visible.map(row).join("")}</div>` : empty(query ? "Ничего не найдено" : "Пациентов пока нет", query ? "Попробуйте изменить запрос поиска." : "Создайте первую карточку пациента — она будет привязана к вашему профилю.", "users-round").replace('<section class="panel">', '').replace('</section>', '')}</section></section>`;
    icon();
  }
  const formatDate = (value) => value ? new Date(`${value}T00:00:00`).toLocaleDateString("ru-RU") : "Не указано";
  const detailField = (label, value) => `<div class="detail-field"><dt>${label}</dt><dd>${escape(value || "Не указано")}</dd></div>`;
  function planSummary(plan) { return `<article class="treatment-card"><div><strong>${escape(plan.title)}</strong><span>${escape(plan.status)} · ${plan.duration_days || "—"} дней · старт ${formatDate(plan.starts_on)}</span></div><button class="compact-button" data-open-plan="${plan.id}">Открыть</button></article>`; }
  async function showPatientDetail(patient) {
    if (!patient) return;
    state.currentPatient = patient;
    try { state.plans = await request("/treatment-plans"); } catch (_) { state.plans = []; }
    const plans = state.plans.filter((plan) => plan.patient_id === patient.id);
    const age = patient.birth_date ? Math.floor((Date.now() - new Date(`${patient.birth_date}T00:00:00`)) / 31557600000) : null;
    $("#patient-detail-title").textContent = patient.full_name;
    $("#patient-detail-content").innerHTML = `<div class="patient-identity"><span class="patient-avatar">${escape(patient.first_name?.charAt(0))}</span><div><h3>${escape(patient.full_name)}</h3><p>Пациент №${escape(patient.id)} · ${age === null ? "Возраст не указан" : `${age} лет`}</p></div></div><section class="detail-section"><div class="detail-actions"><h3>Лечение</h3><button class="compact-button" id="assign-treatment"><i data-lucide="plus"></i>Назначить</button></div><div class="treatment-list">${plans.length ? plans.map(planSummary).join("") : `<p class="detail-meta">Лечение пока не назначено.</p>`}</div></section><section class="detail-section"><h3>Основные данные</h3><dl class="detail-grid">${detailField("Дата рождения", formatDate(patient.birth_date))}${detailField("Пол", patient.sex === "male" ? "Мужской" : patient.sex === "female" ? "Женский" : patient.sex === "other" ? "Другой" : "Не указан")}${detailField("Телефон", patient.phone)}${detailField("Email", patient.email)}${detailField("Экстренный контакт", patient.emergency_contact)}</dl></section><section class="detail-section"><h3>Медицинский контекст</h3><dl class="detail-grid">${detailField("Диагноз / повод обращения", patient.diagnosis)}${detailField("Дата диагноза", formatDate(patient.diagnosis_date))}${detailField("Начало лечения", formatDate(patient.treatment_start_date))}${detailField("Рост", patient.height_cm ? `${patient.height_cm} см` : null)}${detailField("Вес", patient.weight_kg ? `${patient.weight_kg} кг` : null)}${detailField("Аллергии", patient.allergies)}${detailField("Противопоказания", patient.contraindications)}${detailField("Сопутствующие заболевания", patient.comorbidities)}${detailField("Заметки врача", patient.doctor_notes)}</dl></section><p class="detail-meta">Карточка создана ${formatDate(patient.created_at?.slice(0, 10))}. Согласие на обработку данных зафиксировано.</p>`;
    $("#patient-detail-layer").classList.remove("is-hidden"); icon();
  }
  function hidePatientDetail() { $("#patient-detail-layer").classList.add("is-hidden"); }
  async function showPlanForm() {
    state.templates = await request("/treatment-templates");
    $("#plan-template").innerHTML = `<option value="">Индивидуальный план без шаблона</option>${state.templates.map((template) => `<option value="${template.id}">${escape(template.title)}${template.default_duration_days ? ` · ${template.default_duration_days} дн.` : ""}</option>`).join("")}`;
    $("#plan-form").reset(); $("#plan-form [name=starts_on]").value = new Date().toISOString().slice(0, 10); $("#plan-form-error").textContent = ""; $("#plan-form-layer").classList.remove("is-hidden"); icon();
  }
  function hidePlanForm() { $("#plan-form-layer").classList.add("is-hidden"); }
  async function showPlanEditor(planId) {
    const plan = await request(`/treatment-plans/${planId}`);
    $("#plan-editor-title").textContent = plan.title;
    const dayMarkup = plan.days.map((day) => `<article class="plan-day"><h3>День ${day.day_number}${day.title ? ` · ${escape(day.title)}` : ""}</h3>${day.blocks.map((block) => `<div class="plan-item">${escape(block.title)}${block.question ? ` · вопрос: ${escape(block.question)}` : ""}</div>`).join("")}${day.medications.map((medication) => `<div class="plan-item">${escape(medication.medication_name)} · ${escape(medication.dosage || "дозировка не указана")} ${medication.scheduled_time || ""}</div>`).join("")}</article>`).join("");
    const dayOptions = plan.days.map((day) => `<option value="${day.day_number}">День ${day.day_number}</option>`).join("");
    $("#plan-editor-content").innerHTML = `<form class="inline-form" id="plan-status-form"><label class="field-label">Название<input class="input" name="title" value="${escape(plan.title)}" /></label><label class="field-label">Статус<select class="input" name="status"><option value="active" ${plan.status === "active" ? "selected" : ""}>Активен</option><option value="paused" ${plan.status === "paused" ? "selected" : ""}>На паузе</option><option value="completed" ${plan.status === "completed" ? "selected" : ""}>Завершён</option></select></label><button class="button button-secondary" type="submit">Сохранить изменения</button></form><section class="detail-section"><h3>Добавить в план</h3><div class="editor-actions"><form class="inline-form" id="add-block-form"><label class="field-label">День<select class="input" name="day_number">${dayOptions}</select></label><label class="field-label">Тип блока<select class="input" name="block_type"><option value="exercise">Упражнение</option><option value="text">Текст</option><option value="video">Видео</option><option value="pdf">PDF</option><option value="question">Вопрос</option><option value="checklist">Чеклист</option><option value="photo">Фото</option><option value="link">Ссылка</option></select></label><label class="field-label">Название<input class="input" name="title" required /></label><label class="field-label">Вопрос пациенту<input class="input" name="question" /></label><button class="compact-button" type="submit">Добавить задание</button></form><form class="inline-form" id="add-medication-form"><label class="field-label">День<select class="input" name="day_number">${dayOptions}</select></label><label class="field-label">Лекарство<input class="input" name="medication_name" required /></label><label class="field-label">Дозировка<input class="input" name="dosage" /></label><label class="field-label">Время<input class="input" name="scheduled_time" type="time" /></label><label class="field-label">Вопрос пациенту<input class="input" name="question" /></label><button class="compact-button" type="submit">Добавить приём</button></form></div></section><section class="detail-section"><h3>Дни плана</h3><div class="plan-days">${dayMarkup}</div></section>`;
    $("#plan-editor-layer").dataset.planId = plan.id; $("#plan-editor-layer").classList.remove("is-hidden"); icon();
  }
  function hidePlanEditor() { $("#plan-editor-layer").classList.add("is-hidden"); }
  async function renderCurrent() {
    $("#page-title").textContent = state.view === "overview" ? "Обзор" : "Мои пациенты";
    $("#page-section").textContent = state.view === "overview" ? "Рабочее пространство" : "Пациенты";
    loading();
    try { const [patients, plans] = await Promise.all([request("/patients"), request("/treatment-plans")]); state.patients = patients; state.plans = plans; state.view === "overview" ? renderOverview() : renderPatients(); } catch (error) { $("#page-content").innerHTML = empty("Не удалось загрузить данные", error.message, "triangle-alert"); icon(); }
  }
  function showModal() { $("#patient-form").reset(); $("#patient-error").textContent = ""; $("#modal-layer").classList.remove("is-hidden"); icon(); }
  function hideModal() { $("#modal-layer").classList.add("is-hidden"); }
  $("#login-form").addEventListener("submit", async (event) => {
    event.preventDefault(); const button = $("#login-button"); button.disabled = true; $("#login-error").textContent = "";
    try {
      const response = await fetch(`${API}/auth/login`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(Object.fromEntries(new FormData(event.currentTarget))) });
      if (!response.ok) throw new Error("Проверьте логин и пароль.");
      state.token = (await response.json()).access_token; state.user = await request("/auth/me");
      if (state.user.is_admin) throw new Error("Для системного администратора используйте админ-панель.");
      sessionStorage.setItem("nepres_doctor_token", state.token); $("#account-name").textContent = state.user.full_name; $("#account-avatar").textContent = state.user.full_name.charAt(0).toUpperCase(); setScreen(true); renderCurrent();
    } catch (error) { sessionStorage.removeItem("nepres_doctor_token"); state.token = null; $("#login-error").textContent = error.message; } finally { button.disabled = false; }
  });
  document.querySelectorAll(".nav-item[data-view]").forEach((button) => button.addEventListener("click", () => { state.view = button.dataset.view; document.querySelectorAll(".nav-item[data-view]").forEach((item) => item.classList.toggle("is-active", item === button)); renderCurrent(); }));
  $("#refresh-button").addEventListener("click", renderCurrent); $("#search-input").addEventListener("input", () => { if (state.view === "patients") renderPatients(); });
  $("#new-patient-button").addEventListener("click", showModal); $("#modal-close").addEventListener("click", hideModal); $("#modal-cancel").addEventListener("click", hideModal); $("#modal-layer").addEventListener("click", (event) => { if (event.target === event.currentTarget) hideModal(); });
  $("#page-content").addEventListener("click", (event) => { const row = event.target.closest("[data-patient-id]"); if (row) showPatientDetail(state.patients.find((patient) => patient.id === Number(row.dataset.patientId))); });
  $("#patient-detail-close").addEventListener("click", hidePatientDetail); $("#patient-detail-layer").addEventListener("click", (event) => { if (event.target === event.currentTarget) hidePatientDetail(); });
  $("#patient-detail-content").addEventListener("click", (event) => { if (event.target.closest("#assign-treatment")) showPlanForm(); const plan = event.target.closest("[data-open-plan]"); if (plan) showPlanEditor(plan.dataset.openPlan); });
  $("#plan-form-close").addEventListener("click", hidePlanForm); $("#plan-form-cancel").addEventListener("click", hidePlanForm); $("#plan-form-layer").addEventListener("click", (event) => { if (event.target === event.currentTarget) hidePlanForm(); });
  $("#plan-form").addEventListener("submit", async (event) => {
    event.preventDefault(); const fields = Object.fromEntries(new FormData(event.currentTarget)); fields.patient_id = state.currentPatient.id; fields.template_id = fields.template_id ? Number(fields.template_id) : null; fields.duration_days = fields.duration_days ? Number(fields.duration_days) : null;
    try { await request("/treatment-plans", { method: "POST", body: JSON.stringify(fields) }); hidePlanForm(); await showPatientDetail(state.currentPatient); } catch (error) { $("#plan-form-error").textContent = error.message; }
  });
  $("#plan-editor-close").addEventListener("click", hidePlanEditor); $("#plan-editor-layer").addEventListener("click", (event) => { if (event.target === event.currentTarget) hidePlanEditor(); });
  $("#plan-editor-content").addEventListener("submit", async (event) => { event.preventDefault(); const planId = $("#plan-editor-layer").dataset.planId; const data = Object.fromEntries(new FormData(event.target)); if (event.target.id === "plan-status-form") await request(`/treatment-plans/${planId}`, { method: "PATCH", body: JSON.stringify(data) }); if (event.target.id === "add-block-form") { const day = data.day_number; delete data.day_number; data.question ||= null; await request(`/treatment-plans/${planId}/days/${day}/blocks`, { method: "POST", body: JSON.stringify(data) }); } if (event.target.id === "add-medication-form") { const day = data.day_number; delete data.day_number; data.dosage ||= null; data.scheduled_time ||= null; data.question ||= null; await request(`/treatment-plans/${planId}/days/${day}/medications`, { method: "POST", body: JSON.stringify(data) }); } await showPlanEditor(planId); });
  $("#patient-form").addEventListener("submit", async (event) => {
    event.preventDefault(); const button = $("#patient-submit"); const fields = Object.fromEntries(new FormData(event.currentTarget));
    ["phone","email","height_cm","weight_kg","diagnosis_date","contraindications","comorbidities","allergies"].forEach((key) => { if (!fields[key]) fields[key] = null; });
    if (fields.height_cm) fields.height_cm = Number(fields.height_cm); if (fields.weight_kg) fields.weight_kg = Number(fields.weight_kg); fields.consent_to_data_processing = fields.consent_to_data_processing === "on";
    button.disabled = true; $("#patient-error").textContent = "";
    try { await request("/patients", { method:"POST", body:JSON.stringify(fields) }); hideModal(); state.view = "patients"; document.querySelectorAll(".nav-item[data-view]").forEach((item) => item.classList.toggle("is-active", item.dataset.view === "patients")); renderCurrent(); } catch (error) { $("#patient-error").textContent = error.message; } finally { button.disabled = false; }
  });
  $("#logout-button").addEventListener("click", () => { sessionStorage.removeItem("nepres_doctor_token"); state.token = null; state.patients = []; $("#login-form").reset(); setScreen(false); });
  (async () => { if (!state.token) return icon(); try { state.user = await request("/auth/me"); if (state.user.is_admin) throw new Error(); $("#account-name").textContent = state.user.full_name; $("#account-avatar").textContent = state.user.full_name.charAt(0).toUpperCase(); setScreen(true); renderCurrent(); } catch (_) { sessionStorage.removeItem("nepres_doctor_token"); state.token = null; icon(); } })();
})();
