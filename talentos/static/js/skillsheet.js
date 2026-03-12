/**
 * スキルシート画面ロジック
 */

// --- 状態 ---
var ssState = {
  data: null,
  conversationId: "",
  currentTheme: "basic",
  isLoading: false,
};

var THEME_ORDER = ["basic", "career", "skills"];

// --- DOM ---
var ssMessages = document.getElementById("ss-messages");
var ssInput = document.getElementById("ss-message-input");
var ssSendBtn = document.getElementById("ss-send-btn");
var ssBasicInfo = document.getElementById("ss-basic-info");
var ssSkillTags = document.getElementById("ss-skill-tags");
var ssCareerList = document.getElementById("ss-career-list");
var ssOptSection = document.getElementById("ss-optimization");
var ssOptCards = document.getElementById("ss-opt-cards");

// --- 初期化 ---
document.addEventListener("DOMContentLoaded", function () {
  loadSkillSheet();

  ssSendBtn.addEventListener("click", ssSendMessage);
  ssInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      ssSendMessage();
    }
  });
  ssInput.addEventListener("input", function () {
    ssInput.style.height = "auto";
    ssInput.style.height = Math.min(ssInput.scrollHeight, 120) + "px";
  });

  document.getElementById("btn-save").addEventListener("click", saveSheet);
  document.getElementById("btn-pdf").addEventListener("click", downloadPdf);

  // 初回チャットメッセージ
  ssAppendAi("スキルシートの編集をお手伝いします。変更したい内容を教えてください。");
});

// --- データ読み込み ---
async function loadSkillSheet() {
  var engineerId = window.__TARGET_ENGINEER_ID__ || window.__USER__.user_id;
  try {
    var res = await fetch("/api/skillsheet/" + engineerId);
    if (res.status === 404) {
      ssBasicInfo.innerHTML = '<p class="ss-placeholder">まだヒアリングが完了していません。AIヒアリング画面でデータを作成してください。</p>';
      return;
    }
    ssState.data = await res.json();
    renderPreview();
  } catch (e) {
    ssBasicInfo.innerHTML = '<p class="ss-placeholder">データの読み込みに失敗しました。</p>';
  }
}

// --- プレビュー描画 ---
function renderPreview() {
  var d = ssState.data;
  if (!d) return;

  // 基本情報
  var basic = d.basic || {};
  var basicHtml = "";
  var fields = [
    ["氏名", d.name],
    ["専門分野", d.specialty || basic.specialty],
    ["最終学歴", [basic.school_name, basic.faculty_name].filter(Boolean).join(" ")],
    ["勤務地", basic.work_location],
    ["最寄駅", basic.nearest_station],
    ["スキルレベル", basic.skill_level],
    ["自己PR", basic.self_pr],
  ];
  fields.forEach(function (f) {
    if (f[1]) {
      basicHtml +=
        '<div class="ss-info-row">' +
          '<span class="ss-info-label">' + ssEsc(f[0]) + '：</span>' +
          '<span class="ss-info-value">' + ssEsc(f[1]) + '</span>' +
        '</div>';
    }
  });
  ssBasicInfo.innerHTML = basicHtml || '<p class="ss-placeholder">基本情報なし</p>';

  // 主要スキル
  var allSkills = [];
  (d.career || []).forEach(function (c) {
    (c.tech_stack || []).forEach(function (t) {
      if (allSkills.indexOf(t) === -1) allSkills.push(t);
    });
  });
  var sk = d.skills || {};
  (sk.tools || []).forEach(function (t) { if (allSkills.indexOf(t) === -1) allSkills.push(t); });
  (sk.certifications || []).forEach(function (t) { if (allSkills.indexOf(t) === -1) allSkills.push(t); });

  if (allSkills.length > 0) {
    ssSkillTags.innerHTML = allSkills.map(function (s) {
      return '<span class="ss-skill-tag">' + ssEsc(s) + '</span>';
    }).join("");
  } else {
    ssSkillTags.innerHTML = '<p class="ss-placeholder">ヒアリング後に表示されます</p>';
  }

  // 職務経歴
  var careers = d.career || [];
  if (careers.length > 0) {
    var html = "";
    careers.forEach(function (c) {
      var techs = (c.tech_stack || []).map(function (t) {
        return '<span class="ss-tech-tag">' + ssEsc(t) + '</span>';
      }).join("");
      html +=
        '<div class="ss-career-card">' +
          '<div class="ss-career-top">' +
            '<span class="ss-career-project">' + ssEsc(c.project_name || "") + '</span>' +
            '<span class="ss-career-period">' + ssEsc(c.period_start || "") + ' 〜 ' + ssEsc(c.period_end || "") + '</span>' +
          '</div>' +
          '<div class="ss-career-meta">' +
            '<span>&#128100; ' + ssEsc(c.role_title || "") + '</span>' +
            '<span>&#128101; ' + (c.team_size || "—") + '名</span>' +
          '</div>' +
          '<div class="ss-career-techs">' + techs + '</div>' +
          '<div class="ss-career-desc">' + ssEsc(c.description || "") + '</div>' +
        '</div>';
    });
    html += '<div class="ss-career-adding">+ 経歴を追加中...</div>';
    ssCareerList.innerHTML = html;
  } else {
    ssCareerList.innerHTML = '<p class="ss-placeholder">ヒアリング後に表示されます</p>';
  }

  // 最適化提案
  var opt = d.optimized || {};
  if (Object.keys(opt).length > 0) {
    ssOptSection.style.display = "";
    var optHtml = "";
    Object.keys(opt).forEach(function (theme) {
      var themeData = opt[theme];
      var label = theme === "basic" ? "基本情報" : theme === "career" ? "職務経歴" : "スキル・資格";
      optHtml +=
        '<div class="ss-opt-card">' +
          '<div class="ss-opt-card-title">' + ssEsc(label) + ' 最適化候補</div>' +
          '<div class="ss-opt-card-body">' + ssEsc(JSON.stringify(themeData).substring(0, 200)) + '</div>' +
        '</div>';
    });
    ssOptCards.innerHTML = optHtml;
  }
}

// --- チャット ---
function ssAppendAi(text) {
  var el = document.createElement("div");
  el.className = "ss-msg ai";
  el.innerHTML =
    '<div class="ss-ai-avatar">AI</div>' +
    '<div class="ss-bubble">' + ssEsc(text) + '</div>';
  ssMessages.appendChild(el);
  ssMessages.scrollTop = ssMessages.scrollHeight;
}

function ssAppendUser(text) {
  var initials = (window.__USER__ && window.__USER__.name ? window.__USER__.name[0] : "U");
  var el = document.createElement("div");
  el.className = "ss-msg user";
  el.innerHTML =
    '<div class="ss-user-avatar">' + ssEsc(initials) + '</div>' +
    '<div class="ss-bubble">' + ssEsc(text) + '</div>';
  ssMessages.appendChild(el);
  ssMessages.scrollTop = ssMessages.scrollHeight;
}

function ssShowTyping() {
  var el = document.createElement("div");
  el.className = "ss-typing";
  el.id = "ss-typing";
  el.innerHTML =
    '<div class="ss-ai-avatar">AI</div>' +
    '<div class="ss-bubble">' +
      '<div class="ss-typing-dot"></div>' +
      '<div class="ss-typing-dot"></div>' +
      '<div class="ss-typing-dot"></div>' +
    '</div>';
  ssMessages.appendChild(el);
  ssMessages.scrollTop = ssMessages.scrollHeight;
}

function ssHideTyping() {
  var el = document.getElementById("ss-typing");
  if (el) el.remove();
}

async function ssSendMessage() {
  var text = ssInput.value.trim();
  if (!text || ssState.isLoading) return;

  ssState.isLoading = true;
  ssSendBtn.disabled = true;
  ssInput.value = "";
  ssInput.style.height = "auto";

  ssAppendUser(text);
  ssShowTyping();

  try {
    var res = await fetch("/api/hearing/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        theme: ssState.currentTheme,
        message: text,
        conversation_id: ssState.conversationId,
      }),
    });
    var data = await res.json();
    ssHideTyping();

    if (data.conversation_id) {
      ssState.conversationId = data.conversation_id;
    }

    ssAppendAi(data.message);

    // テーマ完了 → プレビュー更新
    if (data.theme_completed && data.sheet_update) {
      updatePreviewFromChat(data.sheet_update);

      var idx = THEME_ORDER.indexOf(ssState.currentTheme);
      if (idx < THEME_ORDER.length - 1) {
        ssState.currentTheme = THEME_ORDER[idx + 1];
        ssState.conversationId = "";
      }

      // データ再読み込み
      await loadSkillSheet();
    }
  } catch (e) {
    ssHideTyping();
    ssAppendAi("通信エラーが発生しました。");
  } finally {
    ssState.isLoading = false;
    ssSendBtn.disabled = false;
    ssInput.focus();
  }
}

function updatePreviewFromChat(sheetUpdate) {
  // sheet_update.data が来たらstateにマージして再描画
  if (!ssState.data) {
    ssState.data = {
      engineer_id: window.__USER__.user_id,
      name: window.__USER__.name,
      specialty: "",
      basic: {},
      career: [],
      skills: {},
      optimized: {},
    };
  }

  var theme = sheetUpdate.theme;
  var data = sheetUpdate.data;

  if (theme === "basic") {
    ssState.data.basic = data;
    ssState.data.specialty = data.specialty || ssState.data.specialty;
  } else if (theme === "career") {
    if (data.project_name) {
      ssState.data.career.push(data);
    }
  } else if (theme === "skills") {
    ssState.data.skills = data;
  }

  renderPreview();
}

// --- 保存 ---
async function saveSheet() {
  if (!ssState.data) {
    alert("保存するデータがありません。");
    return;
  }

  var btn = document.getElementById("btn-save");
  var originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = "保存中...";

  try {
    var res = await fetch("/api/skillsheet/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        engineer_id: window.__TARGET_ENGINEER_ID__ || window.__USER__.user_id,
        basic: ssState.data.basic || null,
        career: ssState.data.career || null,
        skills: ssState.data.skills || null,
      }),
    });
    var result = await res.json();
    if (result.success) {
      btn.textContent = "保存しました \u2713";
      showToast("保存しました");
      setTimeout(function () {
        btn.textContent = originalText;
        btn.disabled = false;
      }, 2000);
    } else {
      btn.textContent = originalText;
      btn.disabled = false;
      alert(result.detail || "保存に失敗しました。");
    }
  } catch (e) {
    btn.textContent = originalText;
    btn.disabled = false;
    alert("データの保存に失敗しました。");
  }
}

function showToast(msg) {
  var toast = document.createElement("div");
  toast.className = "ss-save-toast";
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(function () { toast.remove(); }, 2500);
}

// --- PDF ---
function downloadPdf() {
  var engineerId = window.__USER__.user_id;
  window.open("/api/skillsheet/" + engineerId + "/pdf", "_blank");
}

// --- ユーティリティ ---
function ssEsc(str) {
  var div = document.createElement("div");
  div.textContent = str || "";
  return div.innerHTML;
}
