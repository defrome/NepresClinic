(() => {
  const app = document.querySelector("#app");
  const toast = document.querySelector("#toast");
  const token = location.pathname.split("/").filter(Boolean).pop();
  let state;
  const typeMeta = { text:["file-text","Инструкция","Подробнее"], video:["play-circle","Видео","Посмотреть видео"], pdf:["file-text","PDF-документ","Открыть PDF"], exercise:["dumbbell","Упражнение","Открыть инструкцию"], question:["message-circle","Вопрос врача","Ответить"], checklist:["list-checks","Чеклист","Открыть чеклист"], photo:["camera","Фото","Загрузить фото"], link:["link","Материал","Открыть ссылку"] };
  const escape = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", "'":"&#39;", '"':"&quot;" }[character]));
  const icons = () => window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });
  const time = (value) => value ? new Date(value).toLocaleTimeString("ru-RU", { hour:"2-digit", minute:"2-digit" }) : "";
  const api = async (path, options = {}) => {
    const response = await fetch(`/api/v1/patient-access/${token}${path}`, { ...options, headers: { "Content-Type":"application/json", ...(options.headers || {}) } });
    if (!response.ok) { const body = await response.json().catch(() => ({})); const error = new Error(body.detail || "Не удалось выполнить запрос"); error.status = response.status; throw error; }
    return response.status === 204 ? null : response.json();
  };
  function notify(message) { toast.textContent = message; toast.classList.add("is-visible"); window.setTimeout(() => toast.classList.remove("is-visible"), 3000); }
  function percentage() { return state.total_count ? Math.round(state.completed_count / state.total_count * 100) : null; }
  function itemBy(kind, id) { return (kind === "medication" ? state.medications : state.blocks).find((item) => item.id === Number(id)); }
  function nextAction() {
    const timed = state.medications.filter((item) => !item.completed).sort((a, b) => (a.scheduled_time || "99:99").localeCompare(b.scheduled_time || "99:99"))[0];
    const block = state.blocks.find((item) => !item.completed);
    return timed ? `${timed.scheduled_time || "В течение дня"} — ${timed.medication_name}` : block ? block.title : null;
  }
  function completedText(item, medicine = false) { return item.completed_at ? `${medicine ? "Принято" : "Выполнено"} сегодня в ${time(item.completed_at)}` : (medicine ? "Приём отмечен" : "Выполнено"); }
  function resource(item, label) { return item.resource_url ? `<a class="material-link" href="${escape(item.resource_url)}" target="_blank" rel="noreferrer"><i data-lucide="external-link"></i>${label}</a>` : ""; }
  function taskCard(item) {
    const [icon, label, action] = typeMeta[item.block_type] || typeMeta.text;
    const requiredAnswer = Boolean(item.question && item.is_required);
    return `<article class="task-card ${item.completed ? "is-done" : ""}" id="block-${item.id}" data-card="block" data-id="${item.id}">
      <div class="item-head"><span class="kind"><i data-lucide="${icon}"></i></span><div class="item-copy"><span class="item-type">${label}${item.is_required ? " · обязательно" : " · дополнительно"}</span><h3>${escape(item.title)}</h3>${item.content ? `<p>${escape(item.content)}</p>` : ""}</div></div>
      ${resource(item, action)}
      ${item.question ? `<div class="question"><label for="answer-block-${item.id}">${escape(item.question)}${requiredAnswer ? " *" : ""}</label>${item.completed ? `<p class="saved-answer">${item.answer ? `Ответ отправлен: ${escape(item.answer)}` : "Выполнено без ответа"}</p>` : `<textarea id="answer-block-${item.id}" data-answer-for="block-${item.id}" placeholder="${requiredAnswer ? "Введите ответ" : "Ответ необязательный"}"></textarea>`}</div>` : ""}
      ${item.completed ? `<div class="completion"><span><i data-lucide="check-circle-2"></i>${completedText(item)}</span><button class="text-button" data-action="undo" data-kind="block" data-id="${item.id}">Отменить отметку</button></div>` : `<button class="primary-button" data-action="complete" data-kind="block" data-id="${item.id}" ${requiredAnswer ? "disabled" : ""}><i data-lucide="check"></i>Отметить выполненным</button>`}
    </article>`;
  }
  function medicineCard(item) {
    const requiredAnswer = Boolean(item.question && item.is_required);
    return `<article class="medicine-card ${item.completed ? "is-done" : ""}" id="medication-${item.id}" data-card="medication" data-id="${item.id}">
      <span class="medicine-time">${escape(item.scheduled_time || "В течение дня")}</span><div class="medicine-copy"><span class="item-type">По времени${item.is_required ? " · обязательно" : ""}</span><h3>${escape(item.medication_name)}</h3><p>${escape(item.dosage || "Дозировка и способ приёма не указаны")}</p>${item.question ? `<label class="medicine-question" for="answer-medication-${item.id}">${escape(item.question)}${requiredAnswer ? " *" : ""}</label>${item.completed ? (item.answer ? `<p class="saved-answer">Ответ отправлен: ${escape(item.answer)}</p>` : "") : `<textarea id="answer-medication-${item.id}" data-answer-for="medication-${item.id}" placeholder="${requiredAnswer ? "Введите ответ" : "Ответ необязательный"}"></textarea>`}` : ""}</div>
      <div class="medicine-action">${item.completed ? `<span class="taken"><i data-lucide="check-circle-2"></i>${completedText(item, true)}</span><button class="text-button" data-action="undo" data-kind="medication" data-id="${item.id}">Отменить</button>` : `<button class="secondary-button" data-action="complete" data-kind="medication" data-id="${item.id}" ${requiredAnswer ? "disabled" : ""}><i data-lucide="check"></i>Отметить приём</button>`}</div>
    </article>`;
  }
  function updateSummary() {
    const percent = percentage();
    const ring = document.querySelector(".ring");
    if (ring) { ring.style.setProperty("--progress", `${percent || 0}%`); ring.querySelector("span").textContent = percent === null ? "—" : `${percent}%`; }
    const progress = document.querySelector("#today-progress"); if (progress) progress.textContent = state.total_count ? `${state.completed_count} из ${state.total_count} выполнено` : "Новых заданий нет";
    const remaining = document.querySelector("#remaining"); if (remaining) remaining.textContent = state.total_count ? `Осталось сегодня: ${Math.max(0, state.total_count - state.completed_count)}` : "Следующий день начнётся завтра";
    const heroAction = document.querySelector("#hero-action"); if (heroAction) heroAction.textContent = nextAction() ? `Первое действие: ${nextAction()}` : "На сегодня всё готово";
  }
  function patchItem(kind, id) { const old = document.querySelector(`#${kind}-${id}`); if (!old) return; const item = itemBy(kind, id); old.outerHTML = kind === "medication" ? medicineCard(item) : taskCard(item); updateSummary(); icons(); }
  function render(data) {
    state = data;
    const percent = percentage(); const first = nextAction(); const courseProgress = state.course_total_count ? `${state.course_completed_count} из ${state.course_total_count}` : "план готов";
    app.innerHTML = `<header class="hero"><div class="topline"><span>Nepres Clinic</span><span>День ${state.day_number}${state.duration_days ? ` из ${state.duration_days}` : ""}</span></div><h1>Здравствуйте, ${escape(state.patient_name.split(" ")[0])}</h1><p class="plan-name">${escape(state.plan_title)}</p><div class="progress-row"><div class="ring" style="--progress:${percent || 0}%"><span>${percent === null ? "—" : `${percent}%`}</span></div><div class="progress-copy"><strong>${state.total_count ? `Сегодня нужно выполнить ${state.total_count} ${state.total_count === 1 ? "действие" : "действия"}` : "На сегодня всё готово"}</strong><span id="hero-action">${escape(first ? `Первое действие: ${first}` : "Новых заданий нет")}</span><small id="today-progress">${state.total_count ? `${state.completed_count} из ${state.total_count} выполнено` : "Новых заданий нет"}</small></div></div><a class="hero-button" href="#tasks"><i data-lucide="arrow-down"></i>${first ? "Перейти к заданиям" : "Посмотреть план"}</a></header>
      <nav class="day-navigation" aria-label="Навигация по дням курса"><button class="secondary-button" data-day="${state.day_number - 1}" aria-label="Предыдущий день" ${state.day_number <= 1 ? "disabled" : ""}><i data-lucide="chevron-left"></i><span>Предыдущий день</span></button><span class="day-current">День ${state.day_number} из ${state.duration_days || "—"}</span><button class="secondary-button" data-day="${state.day_number + 1}" aria-label="Следующий день" ${state.day_number >= (state.duration_days || state.day_number) ? "disabled" : ""}><span>Следующий день</span><i data-lucide="chevron-right"></i></button></nav>
      ${state.previous_day_incomplete ? `<aside class="gentle-banner"><i data-lucide="heart-handshake"></i><p><strong>Вчера осталось невыполненное задание.</strong> Ничего страшного — продолжайте с сегодняшнего дня. Если самочувствие не позволяет выполнить его, напишите врачу.</p></aside>` : ""}
      <section class="course-status"><span><i data-lucide="route"></i>Курс: день ${state.day_number} из ${state.duration_days || "—"}</span><span>${courseProgress} действий за курс</span><span id="remaining">${state.total_count ? `Осталось сегодня: ${state.total_count - state.completed_count}` : "Следующий день начнётся завтра"}</span></section>
      <main id="tasks" class="content">${state.medications.length ? `<section><div class="section-heading"><div><span class="eyebrow">По времени</span><h2>Приём лекарств</h2></div><p>Отмечайте приём после выполнения.</p></div><div class="cards">${state.medications.map(medicineCard).join("")}</div></section>` : ""}<section><div class="section-heading"><div><span class="eyebrow">В течение дня</span><h2>Задания на сегодня</h2></div><p>Обязательные задания отмечены отдельно.</p></div><div class="cards">${state.blocks.map(taskCard).join("") || `<div class="empty"><i data-lucide="calendar-check-2"></i><h2>На сегодня всё готово</h2><p>Новых заданий нет. Если врач добавит их, они появятся здесь.</p></div>`}</div></section></main>
      <aside class="doctor-contact"><div><span class="eyebrow">Связь с врачом</span><h2>Стало хуже или появились вопросы?</h2><p>Свяжитесь с ${escape(state.doctor_name || "вашим врачом")}. При угрозе жизни вызовите 112.</p></div>${state.doctor_email ? `<a class="secondary-button" href="mailto:${escape(state.doctor_email)}"><i data-lucide="mail"></i>Написать врачу</a>` : `<span class="contact-note">Контакт врача уточните в клинике</span>`}</aside>`;
    icons();
  }
  async function changeCompletion(button, undo = false) {
    const { kind, id } = button.dataset; const item = itemBy(kind, id); const card = button.closest("article");
    const answer = document.querySelector(`#answer-${kind}-${id}`)?.value.trim() || null;
    button.disabled = true; button.innerHTML = `<i data-lucide="loader-circle"></i>${undo ? "Отменяем…" : "Сохраняем…"}`; icons();
    try {
      if (undo) { await api(`/${kind}/${id}/complete`, { method:"DELETE" }); item.completed = false; item.completed_at = null; item.answer = null; state.completed_count = Math.max(0, state.completed_count - 1); notify("Отметка отменена"); }
      else { await api(`/${kind}/${id}/complete`, { method:"POST", body:JSON.stringify({ answer }) }); item.completed = true; item.completed_at = new Date().toISOString(); item.answer = answer; state.completed_count += 1; state.course_completed_count += 1; notify(answer ? "Ответ и отметка сохранены" : "Сохранено"); }
      patchItem(kind, id);
    } catch (error) { button.disabled = false; button.textContent = error.message; notify("Не удалось сохранить. Попробуйте ещё раз."); }
  }
  app.addEventListener("input", (event) => { const id = event.target.dataset.answerFor; if (!id) return; const [kind, targetId] = id.split("-"); const button = document.querySelector(`#${id} [data-action=complete]`); if (button) button.disabled = !event.target.value.trim(); });
  app.addEventListener("click", (event) => { const dayButton = event.target.closest("[data-day]"); if (dayButton) { load(Number(dayButton.dataset.day)); return; } const button = event.target.closest("[data-action]"); if (button) changeCompletion(button, button.dataset.action === "undo"); });
  function renderError(error) {
    const expired = /недействительна|устарел/i.test(error.message); const noPlan = /Активный план/i.test(error.message);
    app.innerHTML = `<section class="error"><i data-lucide="${expired ? "link-2-off" : noPlan ? "calendar-clock" : "wifi-off"}"></i><h1>${expired ? "Ссылка недействительна или устарела" : noPlan ? "Сейчас для вас нет назначенного курса" : "Не удалось загрузить план"}</h1><p>${expired ? "Попросите врача отправить новую ссылку." : noPlan ? "Когда врач назначит курс, он появится на этой странице." : "Проверьте интернет-соединение и повторите попытку."}</p>${!expired && !noPlan ? `<button class="primary-button" id="retry"><i data-lucide="refresh-cw"></i>Повторить</button>` : ""}</section>`; icons(); document.querySelector("#retry")?.addEventListener("click", () => load());
  }
  async function load(day = null) { app.innerHTML = `<div class="loading"><i data-lucide="loader-circle"></i><p>Загружаем ваш план</p></div>`; icons(); try { render(await api(day ? `/days/${day}` : "/today")); } catch (error) { renderError(error); } }
  load();
})();
