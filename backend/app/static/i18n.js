// 翻訳データ（サーバーから取得）
let translations = {};
let currentLanguage = 'ja';

// 翻訳データをサーバーから取得
async function loadTranslations() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/translations`);
    if (res.ok) {
      const data = await res.json();
      translations = data.translations || {};
      currentLanguage = data.language || 'ja';

      // DOM更新
      translatePage();
    }
  } catch (e) {
    console.error('翻訳データの読み込みに失敗しました:', e);
  }
}

// 翻訳関数
function t(key, params = {}) {
  const keys = key.split('.');
  let value = translations;

  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k];
    } else {
      return `[Missing: ${key}]`;
    }
  }

  // プレースホルダー置換
  if (typeof value === 'string' && Object.keys(params).length > 0) {
    for (const [k, v] of Object.entries(params)) {
      value = value.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
    }
  }

  return value;
}

// 通貨フォーマット関数
function formatCurrency(amount) {
  const formatted = Math.round(amount).toLocaleString();
  return t('ui.currency_format', { amount: formatted });
}

// ページ全体を翻訳
function translatePage() {
  // data-i18n属性を持つ要素を翻訳
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    el.textContent = t(key);
  });

  // data-i18n-placeholder属性を持つ要素のプレースホルダーを翻訳
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    el.placeholder = t(key);
  });

  // タイトルを翻訳
  document.title = t('ui.app_title');

  // HTML lang属性を更新
  document.documentElement.lang = currentLanguage;
}

// 初期化
document.addEventListener('DOMContentLoaded', () => {
  loadTranslations();
});
