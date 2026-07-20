(() => {
  const API = "/api/v1";
  const state = { token: sessionStorage.getItem("nepres_token"), view: "overview", data: [], user: null, organizations: [], doctors: [], modal: null };
  const $ = (selector) => document.querySelector(selector);
  const icon = () => window.lucide?.createIcons({ attrs: { "stroke-width": 1.75 } });
  const escape = (value) => String(value ?? "—").replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
  const request = async (path, options = {}) => {
    const response = await fetch(`${API}${path}`, { ...options, headers: { "Content-Type": "application/json", Authorization: `Bearer ${state.token}`, ...(options.headers || {}) } });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "Не удалось выполнить запрос");
    }
    return response.status === 204 ? null : response.json();
  };

  function setScreen(authenticated) {
    $("#login-screen").classList.toggle("is-hidden", authenticated);
    $("#admin-app").classList.toggle("is-hidden", !authenticated);
    icon();
  }

  function loading() {
    $("#page-content").innerHTML = `<section class="panel"><div class="loading-state"><i data-lucide="loader-circle"></i><h2>Загружаем данные</h2><p>Пожалуйста, подождите.</p></div></section>`;
    icon();
  }

  function empty(title, text, iconName) {
    return `<section class="panel"><div class="empty-state"><i data-lucide="${iconName}"></i><h2>${title}</h2><p>${text}</p></div></section>`;
  }

  function renderOverview({ organizations, doctors, patients }) {
    $("#page-content").innerHTML = `<section class="overview">
      <div class="stats-grid">
        <article class="stat-card"><span class="stat-label">Организации</span><strong class="stat-value">${organizations}</strong></article>
        <article class="stat-card"><span class="stat-label">Врачи в моей организации</span><strong class="stat-value">${doctors}</strong></article>
        <article class="stat-card"><span class="stat-label">Пациенты в моей организации</span><strong class="stat-value">${patients}</strong></article>
      </div>
      <section class="panel"><div class="panel-heading"><h2>Начало работы</h2><p>Данные обновляются по запросу</p></div><div class="empty-state"><i data-lucide="clipboard-plus"></i><h2>Админ-панель готова к работе</h2><p>Создайте организацию или перейдите к списку врачей и пациентов, чтобы начать управление данными.</p></div></section>
    </section>`;
    icon();
  }

  const schemas = {
    organizations: { title: "Организации", section: "Системное управление", endpoint: "/organizations", action: "Организация", icon: "building-2", columns: [["name", "Название", "is-wide"], ["created_at", "Создана", ""]] },
    doctors: { title: "Врачи", section: "Системное управление", endpoint: "/doctors", action: "Врач", icon: "stethoscope", columns: [["full_name", "ФИО", "is-wide"], ["organization_id", "Организация", ""], ["username", "Логин", ""], ["email", "Email", ""], ["is_active", "Статус", ""]] },
    patients: { title: "Пациенты", section: "Системное управление", endpoint: "/patients", action: "Пациент", icon: "users-round", columns: [["full_name", "ФИО", "is-wide"], ["organization_id", "Организация", ""], ["doctor_id", "Врач", ""], ["contact", "Контакт", ""]] },
  };

  function formatDate(value) {
    return value ? new Intl.DateTimeFormat("ru-RU", { day: "2-digit", month: "2-digit", year: "numeric" }).format(new Date(value)) : "—";
  }
  function cellValue(item, key) {
    if (key === "created_at" || key === "birth_date") return formatDate(item[key]);
    if (key === "is_active") return item[key] ? `<span class="status">Активен</span>` : "Неактивен";
    if (key === "organization_id") return escape(state.organizations.find((organization) => organization.id === item[key])?.name || `#${item[key]}`);
    if (key === "doctor_id") return escape(state.doctors.find((doctor) => doctor.id === item[key])?.full_name || `#${item[key]}`);
    return escape(item[key]);
  }
  function renderTable(view, data) {
    const schema = schemas[view];
    const query = $("#search-input").value.trim().toLowerCase();
    const visible = data.filter((item) => Object.values(item).some((value) => String(value ?? "").toLowerCase().includes(query)));
    const head = schema.columns.map(([, label, className]) => `<div class="table-cell ${className}">${label}</div>`).join("");
    const actionHead = `<div class="table-cell is-actions">Действия</div>`;
    const rows = visible.map((item) => `<div class="table-row">${schema.columns.map(([key, , className]) => `<div class="table-cell ${className}" title="${escape(item[key])}">${cellValue(item, key)}</div>`).join("")}<div class="table-cell is-actions"><button class="table-action" data-edit="${item.id}" aria-label="Редактировать"><i data-lucide="pencil"></i></button><button class="table-action is-danger" data-delete="${item.id}" aria-label="Удалить"><i data-lucide="trash-2"></i></button></div></div>`).join("");
    $("#page-content").innerHTML = `<section class="data-panel"><section class="panel"><div class="panel-heading"><h2>${schema.title}</h2><p>${visible.length} из ${data.length}</p></div>${visible.length ? `<div class="table"><div class="table-row table-head">${head}${actionHead}</div>${rows}</div>` : empty(query ? "Ничего не найдено" : `Нет данных: ${schema.title.toLowerCase()}`, query ? "Попробуйте изменить запрос поиска." : "Список появится после создания первой записи.", schema.icon).replace('<section class="panel">', '').replace('</section>', '')}</section></section>`;
    icon();
  }

  async function renderCurrent() {
    const view = state.view;
    const schema = schemas[view];
    $("#page-title").textContent = view === "overview" ? "Обзор" : schema.title;
    $("#page-section").textContent = view === "overview" ? "Администрирование" : schema.section;
    $("#new-button-label").textContent = view === "overview" ? "Организация" : schema.action;
    loading();
    try {
      if (view === "overview") {
        const [organizations, doctors, patients] = await Promise.all([request("/organizations"), request("/doctors"), request("/patients")]);
        state.organizations = organizations; state.doctors = doctors;
        renderOverview({ organizations: organizations.length, doctors: doctors.length, patients: patients.length });
      } else {
        const [items, organizations, doctors] = await Promise.all([request(schema.endpoint), request("/organizations"), request("/doctors")]);
        state.data = items; state.organizations = organizations; state.doctors = doctors;
        renderTable(view, state.data);
      }
    } catch (error) { $("#page-content").innerHTML = empty("Не удалось загрузить данные", error.message, "triangle-alert"); icon(); }
  }

  function organizationOptions(selectedId) {
    return state.organizations.map((organization) => `<option value="${organization.id}" ${organization.id === selectedId ? "selected" : ""}>${escape(organization.name)}</option>`).join("");
  }
  function doctorOptions(selectedId) {
    return state.doctors.map((doctor) => `<option value="${doctor.id}" ${doctor.id === selectedId ? "selected" : ""}>${escape(doctor.full_name)} — ${escape(state.organizations.find((organization) => organization.id === doctor.organization_id)?.name || `#${doctor.organization_id}`)}</option>`).join("");
  }
  function showModal(item = null) {
    const view = state.view === "overview" ? "organizations" : state.view;
    const label = schemas[view].action;
    state.modal = { view, item };
    const value = (key) => escape(item?.[key] || "");
    let fields;
    if (view === "organizations") fields = `<label class="field-label" for="entry-name">Название организации</label><input class="input" id="entry-name" name="name" value="${value("name")}" minlength="2" required />`;
    else if (view === "doctors" && item) fields = `<label class="field-label" for="entry-full-name">ФИО</label><input class="input" id="entry-full-name" name="full_name" value="${value("full_name")}" minlength="2" required /><label class="field-label" for="entry-email">Email</label><input class="input" id="entry-email" name="email" type="email" value="${value("email")}" /><label class="field-label" for="entry-active">Статус</label><select class="input" id="entry-active" name="is_active"><option value="true" ${item.is_active ? "selected" : ""}>Активен</option><option value="false" ${!item.is_active ? "selected" : ""}>Неактивен</option></select>`;
    else if (view === "doctors") fields = `<label class="field-label" for="entry-organization">Организация</label><select class="input" id="entry-organization" name="organization_id" required>${organizationOptions()}</select><label class="field-label" for="entry-full-name">ФИО</label><input class="input" id="entry-full-name" name="full_name" minlength="2" required /><label class="field-label" for="entry-username">Логин</label><input class="input" id="entry-username" name="username" minlength="3" required /><label class="field-label" for="entry-password">Пароль</label><input class="input" id="entry-password" name="password" type="password" minlength="8" required /><label class="field-label" for="entry-email">Email</label><input class="input" id="entry-email" name="email" type="email" />`;
    else if (item) fields = `<label class="field-label" for="entry-full-name">ФИО</label><input class="input" id="entry-full-name" name="full_name" value="${value("full_name")}" minlength="2" required /><label class="field-label" for="entry-birth-date">Дата рождения</label><input class="input" id="entry-birth-date" name="birth_date" type="date" value="${value("birth_date")}" /><label class="field-label" for="entry-contact">Контакт</label><input class="input" id="entry-contact" name="contact" value="${value("contact")}" /><label class="field-label" for="entry-notes">Заметки</label><input class="input" id="entry-notes" name="notes" value="${value("notes")}" />`;
    else fields = `<label class="field-label" for="entry-organization">Организация</label><select class="input" id="entry-organization" name="organization_id" required>${organizationOptions()}</select><label class="field-label" for="entry-doctor">Врач</label><select class="input" id="entry-doctor" name="doctor_id" required>${doctorOptions()}</select><label class="field-label" for="entry-full-name">ФИО</label><input class="input" id="entry-full-name" name="full_name" minlength="2" required /><label class="field-label" for="entry-birth-date">Дата рождения</label><input class="input" id="entry-birth-date" name="birth_date" type="date" /><label class="field-label" for="entry-contact">Контакт</label><input class="input" id="entry-contact" name="contact" /><label class="field-label" for="entry-notes">Заметки</label><input class="input" id="entry-notes" name="notes" />`;
    $("#modal-title").textContent = item ? `Редактировать: ${label.toLowerCase()}` : `Новый ${label.toLowerCase()}`;
    $("#create-form").innerHTML = `${fields}<p class="form-error" id="create-error" role="alert"></p><div class="modal-actions"><button class="button button-secondary" type="button" id="modal-cancel">Отмена</button><button class="button button-primary" type="submit"><i data-lucide="${item ? "save" : "plus"}"></i><span>${item ? "Сохранить" : "Создать"}</span></button></div>`;
    $("#modal-layer").classList.remove("is-hidden"); icon();
    $("#modal-cancel").onclick = hideModal;
  }
  function hideModal() { $("#modal-layer").classList.add("is-hidden"); }

  $("#login-form").addEventListener("submit", async (event) => {
    event.preventDefault(); const button = $("#login-button"); button.disabled = true; $("#login-error").textContent = "";
    try {
      const form = new FormData(event.currentTarget);
      const response = await fetch(`${API}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(form)) });
      if (!response.ok) throw new Error("Проверьте логин и пароль.");
      state.token = (await response.json()).access_token; sessionStorage.setItem("nepres_token", state.token); state.user = await request("/auth/me");
      $("#account-name").textContent = state.user.full_name; setScreen(true); renderCurrent();
    } catch (error) { $("#login-error").textContent = error.message; } finally { button.disabled = false; }
  });
  document.querySelectorAll(".nav-item[data-view]").forEach((button) => button.addEventListener("click", () => { state.view = button.dataset.view; document.querySelectorAll(".nav-item[data-view]").forEach((item) => item.classList.toggle("is-active", item === button)); renderCurrent(); }));
  $("#refresh-button").addEventListener("click", renderCurrent);
  $("#search-input").addEventListener("input", () => { if (state.view !== "overview") renderTable(state.view, state.data); });
  $("#new-button").addEventListener("click", () => showModal());
  $("#modal-close").addEventListener("click", hideModal);
  $("#modal-layer").addEventListener("click", (event) => { if (event.target === event.currentTarget) hideModal(); });
  $("#create-form").addEventListener("submit", async (event) => {
    event.preventDefault(); const { view, item } = state.modal; const form = Object.fromEntries(new FormData(event.currentTarget));
    Object.keys(form).forEach((key) => { if (!form[key]) form[key] = null; });
    if (form.is_active !== undefined) form.is_active = form.is_active === "true";
    try { await request(`${schemas[view].endpoint}${item ? `/${item.id}` : ""}`, { method: item ? "PATCH" : "POST", body: JSON.stringify(form) }); hideModal(); if (state.view === "overview") state.view = "organizations"; renderCurrent(); } catch (error) { $("#create-error").textContent = error.message; }
  });
  $("#page-content").addEventListener("click", async (event) => {
    const editId = event.target.closest("[data-edit]")?.dataset.edit;
    const deleteId = event.target.closest("[data-delete]")?.dataset.delete;
    if (editId) { showModal(state.data.find((item) => item.id === Number(editId))); return; }
    if (deleteId && window.confirm("Удалить запись? Это действие нельзя отменить.")) {
      try { await request(`${schemas[state.view].endpoint}/${deleteId}`, { method: "DELETE" }); renderCurrent(); } catch (error) { window.alert(error.message); }
    }
  });
  $("#logout-button").addEventListener("click", () => { sessionStorage.removeItem("nepres_token"); state.token = null; state.data = []; $("#login-form").reset(); setScreen(false); });

  (async () => { if (!state.token) return icon(); try { state.user = await request("/auth/me"); $("#account-name").textContent = state.user.full_name; setScreen(true); renderCurrent(); } catch (_) { sessionStorage.removeItem("nepres_token"); state.token = null; icon(); } })();
})();
