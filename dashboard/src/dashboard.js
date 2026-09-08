(() => {
  "use strict";

  const data = JSON.parse(document.getElementById("opic-data").textContent);
  const scoreKeys = ["content", "grammar", "vocabulary", "flow", "delivery"];
  const colors = ["var(--green)", "var(--coral)", "var(--gold)", "var(--blue)", "var(--purple)"];
  const state = { period: "all", selectedPath: data.sessions.at(-1)?.path || "", visibleScores: new Set(scoreKeys) };
  const $ = (selector) => document.querySelector(selector);
  const escapeHtml = (value = "") => String(value).replace(/[&<>'"]/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));

  function sessions() {
    const completed = data.sessions.filter(session => session.status === "completed");
    return state.period === "7" ? completed.slice(-7) : completed;
  }

  function renderSummary(active) {
    const days = new Set(active.map(session => session.date));
    $("#completed-count").textContent = active.length;
    $("#streak-count").textContent = data.metrics.streak;
    $("#vocabulary-count").textContent = data.vocabulary.length;
    $("#review-count").textContent = data.metrics.weekly_review_remaining;
    $("#activity-note").textContent = `${days.size}일 동안 ${active.length}번 연습했어요. 같은 날 여러 번 연습한 기록도 각각 반영합니다.`;
  }

  function renderLegend() {
    $("#score-legend").innerHTML = scoreKeys.map((key, index) => `
      <button type="button" data-score="${key}" aria-pressed="${state.visibleScores.has(key)}" style="--series-color:${colors[index]}">
        <i aria-hidden="true"></i>${escapeHtml(data.metrics.score_labels[key])}
      </button>`).join("");
    document.querySelectorAll("[data-score]").forEach(button => button.addEventListener("click", () => {
      const key = button.dataset.score;
      state.visibleScores.has(key) ? state.visibleScores.delete(key) : state.visibleScores.add(key);
      renderLegend();
      renderScoreChart(sessions());
    }));
  }

  function renderScoreChart(active) {
    const target = $("#score-chart");
    if (!active.length || !active.some(session => Object.keys(session.scores || {}).length)) {
      target.innerHTML = '<div class="empty">점수가 기록되면 성장 추이가 여기에 표시됩니다.</div>';
      return;
    }
    const width = Math.max(520, target.clientWidth || 640);
    const height = 270;
    const margin = { top: 18, right: 20, bottom: 48, left: 38 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const x = index => margin.left + (active.length === 1 ? plotWidth / 2 : index * plotWidth / (active.length - 1));
    const y = value => margin.top + (5 - value) * plotHeight / 4;
    const grid = [1,2,3,4,5].map(value => `<line class="grid" x1="${margin.left}" x2="${width-margin.right}" y1="${y(value)}" y2="${y(value)}"/><text x="${margin.left-12}" y="${y(value)+4}" text-anchor="middle">${value}</text>`).join("");
    const maxLabels = width < 600 ? 3 : 6;
    const step = Math.max(1, Math.ceil(active.length / maxLabels));
    const labels = active.map((session, index) => index % step === 0 || index === active.length - 1
      ? `<text x="${x(index)}" y="${height-17}" text-anchor="middle">${escapeHtml(session.topic.length > 9 ? session.topic.slice(0,9) + "…" : session.topic)}</text>` : "").join("");
    const lines = scoreKeys.map((key, colorIndex) => {
      if (!state.visibleScores.has(key)) return "";
      const points = active.map((session, index) => ({ value: session.scores?.[key], index })).filter(point => Number.isFinite(point.value));
      if (!points.length) return "";
      const path = points.map((point, index) => `${index ? "L" : "M"}${x(point.index)},${y(point.value)}`).join(" ");
      const dots = points.map(point => `<circle cx="${x(point.index)}" cy="${y(point.value)}" r="4" fill="${colors[colorIndex]}"><title>${escapeHtml(active[point.index].topic)} · ${escapeHtml(data.metrics.score_labels[key])} ${point.value}/5</title></circle>`).join("");
      return `<path d="${path}" stroke="${colors[colorIndex]}"/>${dots}`;
    }).join("");
    target.innerHTML = `<svg viewBox="0 0 ${width} ${height}" aria-hidden="true">${grid}<line class="axis" x1="${margin.left}" x2="${width-margin.right}" y1="${height-margin.bottom}" y2="${height-margin.bottom}"/>${lines}${labels}</svg>`;
  }

  function renderCalendar(active) {
    const target = $("#calendar");
    const reference = active.at(-1)?.date ? new Date(`${active.at(-1).date}T00:00:00`) : new Date();
    const year = reference.getFullYear();
    const month = reference.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const counts = active.reduce((acc, session) => (acc[session.date] = (acc[session.date] || 0) + 1, acc), {});
    const weekdays = ["일","월","화","수","목","금","토"].map(day => `<div class="weekday">${day}</div>`).join("");
    const blanks = Array.from({length: firstDay}, () => '<div class="day blank"></div>').join("");
    const cells = Array.from({length: daysInMonth}, (_, index) => {
      const day = index + 1;
      const key = `${year}-${String(month+1).padStart(2,"0")}-${String(day).padStart(2,"0")}`;
      const count = counts[key] || 0;
      return `<div class="day ${count ? "studied" : ""}" data-count="${count > 1 ? count : ""}" title="${key}${count ? ` · ${count}회 연습` : ""}">${day}</div>`;
    }).join("");
    target.innerHTML = weekdays + blanks + cells;
  }

  function aggregateMistakes(active) {
    const map = new Map();
    active.forEach(session => (session.mistakes || []).forEach(mistake => {
      const record = map.get(mistake.id) || { label: mistake.label, count: 0, sessions: 0 };
      record.count += Number(mistake.count || 1);
      record.sessions += 1;
      map.set(mistake.id, record);
    }));
    return [...map.values()].sort((a,b) => b.count-a.count);
  }

  function renderMistakes(active) {
    const mistakes = aggregateMistakes(active);
    if (!mistakes.length) {
      $("#mistake-chart").innerHTML = '<div class="empty">반복 실수가 아직 기록되지 않았어요.</div>';
      return;
    }
    const max = Math.max(...mistakes.map(item => item.count));
    $("#mistake-chart").innerHTML = mistakes.map(item => `
      <div><div class="bar-label"><span>${escapeHtml(item.label)}</span><span>${item.count}회 · ${item.sessions}개 세션</span></div>
      <div class="bar-track"><div class="bar-fill" style="width:${item.count/max*100}%"></div></div></div>`).join("");
  }

  function renderMissions(active) {
    const labels = { success: "성공", partial: "부분 성공", retry: "재도전", unknown: "미평가" };
    const missionColors = { success: "var(--green)", partial: "var(--gold)", retry: "var(--coral)", unknown: "var(--muted)" };
    const counts = active.reduce((acc, session) => {
      const result = session.mission?.result || "unknown";
      acc[result] = (acc[result] || 0) + 1;
      return acc;
    }, {});
    const total = Math.max(1, Object.values(counts).reduce((sum, count) => sum + count, 0));
    const order = ["success", "partial", "retry", "unknown"];
    const segments = order.filter(key => counts[key]).map(key => `<span style="width:${counts[key]/total*100}%;background:${missionColors[key]}" title="${labels[key]} ${counts[key]}회"></span>`).join("");
    const legend = order.filter(key => counts[key]).map(key => `<span><i style="background:${missionColors[key]}"></i>${labels[key]} ${counts[key]}</span>`).join("");
    $("#mission-chart").innerHTML = `<div class="mission-track">${segments}</div><div class="mission-legend">${legend}</div>`;
    const mission = active.at(-1)?.mission?.text || "다음 미션이 아직 기록되지 않았습니다.";
    $("#current-mission").innerHTML = `<span>NEXT FOCUS</span><p>${escapeHtml(mission)}</p>`;
  }

  function renderSessionList(active) {
    if (!active.some(session => session.path === state.selectedPath)) state.selectedPath = active.at(-1)?.path || "";
    $("#session-list").innerHTML = [...active].reverse().map(session => `
      <button type="button" class="session-button" data-session="${escapeHtml(session.path)}" aria-current="${session.path === state.selectedPath}">
        <strong>${escapeHtml(session.topic)}</strong><span>${escapeHtml(session.date)} · ${escapeHtml(session.estimated_level || "평가 없음")}</span>
      </button>`).join("");
    document.querySelectorAll("[data-session]").forEach(button => button.addEventListener("click", () => {
      state.selectedPath = button.dataset.session;
      renderSessionList(sessions());
      renderSessionDetail(sessions().find(session => session.path === state.selectedPath));
    }));
  }

  function renderSessionDetail(session) {
    if (!session) {
      $("#session-detail").innerHTML = '<div class="empty">표시할 세션이 없습니다.</div>';
      return;
    }
    const scoreStrip = scoreKeys.map(key => `<div class="score-chip"><span>${escapeHtml(data.metrics.score_labels[key])}</span><strong>${session.scores?.[key] ?? "–"}</strong></div>`).join("");
    const questions = session.questions.map(question => `<li>${escapeHtml(question)}</li>`).join("");
    const evaluation = session.key_evaluation.map(item => `<li>${escapeHtml(item)}</li>`).join("");
    const improved = session.improved_answers.map(item => `<div class="improved-answer"><strong>${escapeHtml(item.label)}</strong><p>${escapeHtml(item.answer)}</p></div>`).join("");
    const corrections = session.corrections.slice(0, 5).map(item => `<div class="correction"><del>${escapeHtml(item.original)}</del><strong>→ ${escapeHtml(item.recommendation)}</strong></div>`).join("");
    $("#session-detail").innerHTML = `
      <div class="detail-header"><div><h3>${escapeHtml(session.topic)}</h3><p>${escapeHtml(session.date)} · ${escapeHtml(session.input_type.toUpperCase())}</p></div><span class="level-badge">${escapeHtml(session.estimated_level || "N/A")}</span></div>
      <div class="score-strip">${scoreStrip}</div>
      <div class="detail-block"><h4>핵심 평가</h4><ul>${evaluation}</ul></div>
      <div class="detail-block"><h4>질문</h4><ol>${questions}</ol></div>
      <div class="detail-block"><h4>원문과 개선본</h4><div class="answer-compare"><div class="answer-card original"><span>ORIGINAL STT</span><p>${escapeHtml(session.original)}</p></div><div class="answer-card"><span>IMPROVED</span><div class="improved-stack">${improved}</div></div></div></div>
      <div class="detail-block"><h4>주요 교정 일부</h4><div class="correction-list">${corrections}</div></div>`;
  }

  function renderVocabulary() {
    $("#vocabulary-list").innerHTML = [...data.vocabulary].reverse().map(word => `
      <article class="word-card"><div class="word-top"><span>${escapeHtml(word.korean)}</span><span>${word.count}회</span></div>
      <strong>${escapeHtml(word.english)}</strong><p>${escapeHtml(word.example)}</p></article>`).join("");
  }

  function render() {
    const active = sessions();
    renderSummary(active);
    renderScoreChart(active);
    renderCalendar(active);
    renderMistakes(active);
    renderMissions(active);
    renderSessionList(active);
    renderSessionDetail(active.find(session => session.path === state.selectedPath));
  }

  document.querySelectorAll("[data-period]").forEach(button => button.addEventListener("click", () => {
    state.period = button.dataset.period;
    document.querySelectorAll("[data-period]").forEach(item => item.setAttribute("aria-pressed", String(item === button)));
    render();
  }));
  window.addEventListener("resize", () => renderScoreChart(sessions()));
  renderLegend();
  renderVocabulary();
  render();
})();
