/**
 * AIヒアリング画面ロジック
 */

// --- グローバル状態 ---
const state = {
  conversationId: "",
  currentTheme: "basic",
  themeStatus: { basic: "pending", career: "pending", skills: "pending" },
  isLoading: false,
  sheetData: {},
};

const THEME_ORDER = ["basic", "career", "skills"];
const THEME_LABELS = { basic: "基本情報", career: "経歴", skills: "スキル・資格" };

const INITIAL_MESSAGES = {
  basic:  "こんにちは。スキルシートを一緒に作成しましょう。まず、あなたのお名前と専門分野、転勤の可否について教えてください。",
  career: "基本情報の入力が完了しました。次は職務経歴についてお聞きします。直近のプロジェクトから教えてください。",
  skills: "経歴の入力が完了しました。最後に、保有スキル・資格・語学力についてお聞きします。",
};

// --- DOM要素 ---
const messagesArea = document.getElementById("messages-area");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
const skillBarsEl = document.getElementById("skill-bars");
const extractedSection = document.getElementById("extracted-section");
const extractedDataEl = document.getElementById("extracted-data");

// --- 初期化 ---
document.addEventListener("DOMContentLoaded", () => {
  // セッション時刻
  const now = new Date();
  document.getElementById("session-time").textContent =
    "セッション開始: " + now.getFullYear() + "/" +
    String(now.getMonth() + 1).padStart(2, "0") + "/" +
    String(now.getDate()).padStart(2, "0") + " " +
    String(now.getHours()).padStart(2, "0") + ":" +
    String(now.getMinutes()).padStart(2, "0");

  // テーマ進捗を初期更新
  startTheme("basic");

  // 初回AIメッセージ
  appendAiMessage(INITIAL_MESSAGES.basic);

  // イベントリスナー
  sendBtn.addEventListener("click", onSend);
  messageInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  });

  // テキストエリア自動高さ拡張
  messageInput.addEventListener("input", function () {
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";
  });

  // ヒントチップ
  document.querySelectorAll(".hint-chip").forEach(function (chip) {
    chip.addEventListener("click", function () {
      messageInput.value = chip.dataset.text;
      messageInput.focus();
      messageInput.dispatchEvent(new Event("input"));
    });
  });
});

// --- テーマ制御 ---
function startTheme(theme) {
  state.currentTheme = theme;
  state.themeStatus[theme] = "active";
  state.conversationId = "";
  updateThemeProgress();
}

function updateThemeProgress() {
  THEME_ORDER.forEach(function (t) {
    var step = document.getElementById("step-" + t);
    step.classList.remove("active", "completed");
    if (state.themeStatus[t] === "active") step.classList.add("active");
    if (state.themeStatus[t] === "completed") step.classList.add("completed");
  });
}

// --- メッセージ表示 ---
function appendAiMessage(text) {
  var wrapper = document.createElement("div");
  wrapper.className = "message ai";
  wrapper.innerHTML =
    '<div class="ai-avatar">AI</div>' +
    '<div class="msg-bubble">' + escapeHtml(text) + '</div>';
  messagesArea.appendChild(wrapper);
  scrollToBottom();
}

function appendUserMessage(text) {
  var initials = (window.__USER__ && window.__USER__.name ? window.__USER__.name[0] : "U");
  var wrapper = document.createElement("div");
  wrapper.className = "message user";
  wrapper.innerHTML =
    '<div class="user-avatar">' + escapeHtml(initials) + '</div>' +
    '<div class="msg-bubble">' + escapeHtml(text) + '</div>';
  messagesArea.appendChild(wrapper);
  scrollToBottom();
}

function showTyping() {
  var el = document.createElement("div");
  el.className = "typing-indicator";
  el.id = "typing";
  el.innerHTML =
    '<div class="ai-avatar">AI</div>' +
    '<div class="msg-bubble">' +
      '<div class="typing-dot"></div>' +
      '<div class="typing-dot"></div>' +
      '<div class="typing-dot"></div>' +
    '</div>';
  messagesArea.appendChild(el);
  scrollToBottom();
}

function hideTyping() {
  var el = document.getElementById("typing");
  if (el) el.remove();
}

function appendInsightCard(title, items) {
  var tags = items.map(function (i) {
    return '<span class="skill-tag-new">' + escapeHtml(i) + '</span>';
  }).join("");
  var wrapper = document.createElement("div");
  wrapper.className = "message ai";
  wrapper.innerHTML =
    '<div class="ai-avatar">AI</div>' +
    '<div class="msg-bubble">' +
      '<div class="insight-card">' +
        '<div class="insight-title">' + escapeHtml(title) + '</div>' +
        '<div>' + tags + '</div>' +
      '</div>' +
    '</div>';
  messagesArea.appendChild(wrapper);
  scrollToBottom();
}

function scrollToBottom() {
  messagesArea.scrollTop = messagesArea.scrollHeight;
}

function escapeHtml(str) {
  var div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// --- 送信処理 ---
async function onSend() {
  var text = messageInput.value.trim();
  if (!text || state.isLoading) return;

  state.isLoading = true;
  sendBtn.disabled = true;
  messageInput.value = "";
  messageInput.style.height = "auto";

  // 1. ユーザーメッセージ表示
  appendUserMessage(text);

  // 2. タイピングインジケーター
  showTyping();

  try {
    // 3. API呼び出し
    var res = await fetch("/api/hearing/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        theme: state.currentTheme,
        message: text,
        conversation_id: state.conversationId,
      }),
    });
    var data = await res.json();

    // 4. タイピング非表示
    hideTyping();

    // 5. conversation_id 更新
    if (data.conversation_id) {
      state.conversationId = data.conversation_id;
    }

    // 6. AI応答表示
    appendAiMessage(data.message);

    // 7. テーマ完了判定
    if (data.theme_completed) {
      handleThemeCompleted(data);
    }
  } catch (e) {
    hideTyping();
    appendAiMessage("通信エラーが発生しました。もう一度お試しください。");
  } finally {
    state.isLoading = false;
    sendBtn.disabled = false;
    messageInput.focus();
  }
}

// --- テーマ完了時処理 ---
function handleThemeCompleted(data) {
  var theme = state.currentTheme;

  // a. テーマをcompletedに
  state.themeStatus[theme] = "completed";
  updateThemeProgress();

  // b. スキル評価更新
  if (data.sheet_update && data.sheet_update.data) {
    state.sheetData[theme] = data.sheet_update.data;
    updateSkillBars(data.sheet_update);
    updateExtractedData(data.sheet_update);

    // インサイトカード表示
    var tags = extractSkillTags(data.sheet_update);
    if (tags.length > 0) {
      appendInsightCard(THEME_LABELS[theme] + " — 抽出スキル", tags);
    }
  }

  // c. 次のテーマへ
  var currentIdx = THEME_ORDER.indexOf(theme);
  if (currentIdx < THEME_ORDER.length - 1) {
    var nextTheme = THEME_ORDER[currentIdx + 1];
    setTimeout(function () {
      startTheme(nextTheme);
      appendAiMessage(INITIAL_MESSAGES[nextTheme]);
    }, 1000);
  } else {
    // d. 全テーマ完了 → 最適化
    setTimeout(function () { showOptimizeBanner(); }, 1000);
  }
}

function extractSkillTags(sheetUpdate) {
  var data = sheetUpdate.data || {};
  var tags = [];
  if (data.tech_stack) tags = tags.concat(data.tech_stack);
  if (data.tools) tags = tags.concat(data.tools);
  if (data.certifications) tags = tags.concat(data.certifications);
  if (data.specialty) tags.push(data.specialty);
  if (data.skill_level) tags.push(data.skill_level);
  return tags;
}

// --- 右サイドバー更新 ---
function updateSkillBars(sheetUpdate) {
  var data = sheetUpdate.data || {};
  var theme = sheetUpdate.theme;

  var skills = [];
  if (theme === "basic") {
    var levelScore = data.skill_level === "エキスパート" ? 95 : data.skill_level === "上級" ? 80 : data.skill_level === "中級" ? 60 : 40;
    skills.push({ name: "専門性", score: levelScore });
    if (data.self_pr) skills.push({ name: "自己PR充実度", score: Math.min(100, Math.round((data.self_pr.length / 100) * 80)) });
  } else if (theme === "career") {
    skills.push({ name: "リーダーシップ", score: data.team_size ? Math.min(100, data.team_size * 12) : 50 });
    if (data.tech_stack) skills.push({ name: "技術幅", score: Math.min(100, data.tech_stack.length * 22) });
    skills.push({ name: "プロジェクト経験", score: 75 });
  } else if (theme === "skills") {
    if (data.tools) skills.push({ name: "ツール習熟", score: Math.min(100, data.tools.length * 18) });
    if (data.certifications) skills.push({ name: "資格", score: Math.min(100, data.certifications.length * 35) });
    if (data.language_skills) skills.push({ name: "語学力", score: Math.min(100, data.language_skills.length * 40) });
  }

  if (skills.length === 0) return;

  // 既存placeholderを削除
  var placeholder = skillBarsEl.querySelector(".skill-placeholder");
  if (placeholder) placeholder.remove();

  skills.forEach(function (s) {
    var existing = skillBarsEl.querySelector('[data-skill="' + s.name + '"]');
    if (existing) {
      existing.querySelector(".skill-bar-fill").style.width = s.score + "%";
      existing.querySelector(".score-value").textContent = s.score + "%";
    } else {
      var item = document.createElement("div");
      item.className = "skill-bar-item";
      item.dataset.skill = s.name;
      item.innerHTML =
        '<div class="skill-bar-label">' +
          '<span>' + escapeHtml(s.name) + '</span>' +
          '<span class="score-value">' + Math.round(s.score) + '%</span>' +
        '</div>' +
        '<div class="skill-bar-track">' +
          '<div class="skill-bar-fill" style="width: 0%"></div>' +
        '</div>';
      skillBarsEl.appendChild(item);
      // アニメーション
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          item.querySelector(".skill-bar-fill").style.width = Math.round(s.score) + "%";
        });
      });
    }
  });

  // プロフィールタグ更新
  if (data.work_location) {
    document.getElementById("tag-location").textContent = data.work_location.split("、")[0];
  }
  if (data.specialty) {
    document.getElementById("tag-role").textContent = data.specialty;
  }
}

function updateExtractedData(sheetUpdate) {
  var data = sheetUpdate.data || {};
  extractedSection.style.display = "block";

  Object.entries(data).forEach(function (entry) {
    var key = entry[0];
    var val = entry[1];
    var display = val;
    if (Array.isArray(val)) {
      if (val.length > 0 && typeof val[0] === "object") {
        display = val.map(function (v) { return Object.values(v).join(": "); }).join(", ");
      } else {
        display = val.join(", ");
      }
    }
    var item = document.createElement("div");
    item.className = "data-item";
    item.innerHTML =
      '<span class="data-label">' + escapeHtml(key) + '</span>' +
      '<span>' + escapeHtml(String(display)) + '</span>';
    extractedDataEl.appendChild(item);
  });
}

// --- 最適化バナー ---
function showOptimizeBanner() {
  var banner = document.createElement("div");
  banner.className = "optimize-banner";
  banner.innerHTML =
    '<p>全テーマのヒアリングが完了しました！</p>' +
    '<button class="optimize-btn" id="optimize-btn">スキルシートを最適化する</button>';
  messagesArea.appendChild(banner);
  scrollToBottom();

  document.getElementById("optimize-btn").addEventListener("click", runOptimize);
}

async function runOptimize() {
  var btn = document.getElementById("optimize-btn");
  btn.disabled = true;
  btn.textContent = "最適化中...";

  try {
    var res = await fetch("/api/hearing/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ engineer_id: window.__USER__.user_id }),
    });
    var data = await res.json();

    if (data.success) {
      btn.textContent = "最適化完了";
      appendAiMessage("スキルシートの最適化が完了しました。スキルシート管理画面で確認できます。");
      showSkillsheetLink();
    } else {
      btn.textContent = "最適化に失敗しました";
      appendAiMessage("最適化処理でエラーが発生しました。");
    }
  } catch (e) {
    btn.textContent = "エラー";
    appendAiMessage("通信エラーが発生しました。");
  }
}

function showSkillsheetLink() {
  var link = document.createElement("div");
  link.className = "optimize-banner";
  link.style.marginTop = "12px";
  link.innerHTML =
    '<a href="/skillsheet" class="optimize-btn" style="display:inline-block;text-decoration:none;">スキルシートを確認する</a>';
  messagesArea.appendChild(link);
  scrollToBottom();
}
