/**
 * Blauweiss Operations Portal - i18n Configuration
 * Uses i18next for internationalization
 * 
 * Supported languages:
 * - de: Deutsch (German) - Default
 * - en: English
 * - ja: 日本語 (Japanese)
 * - zh: 中文 (Chinese Simplified)
 * - th: ไทย (Thai)
 * - ka: ქართული (Georgian)
 * - hi: हिन्दी (Hindi)
 */

const SUPPORTED_LANGUAGES = {
    de: { name: 'Deutsch', flag: '🇦🇹', dir: 'ltr' },
    en: { name: 'English', flag: '🇺🇸', dir: 'ltr' },
    ja: { name: '日本語', flag: '🇯🇵', dir: 'ltr' },
    zh: { name: '中文', flag: '🇨🇳', dir: 'ltr' },
    th: { name: 'ไทย', flag: '🇹🇭', dir: 'ltr' },
    ka: { name: 'ქართული', flag: '🇬🇪', dir: 'ltr' },
    hi: { name: 'हिन्दी', flag: '🇮🇳', dir: 'ltr' }
};

const DEFAULT_LANGUAGE = 'de';
const FALLBACK_LANGUAGE = 'en';
const STORAGE_KEY = 'blauweiss-portal-lang';

// Translation resources - will be populated by loadTranslations()
let resources = {};

/**
 * Detect user's preferred language
 */
function detectLanguage() {
    // 1. Check localStorage
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && SUPPORTED_LANGUAGES[stored]) {
        return stored;
    }
    
    // 2. Check browser language
    const browserLang = navigator.language?.split('-')[0];
    if (browserLang && SUPPORTED_LANGUAGES[browserLang]) {
        return browserLang;
    }
    
    // 3. Default
    return DEFAULT_LANGUAGE;
}

/**
 * Load translation JSON files
 */
async function loadTranslations() {
    const namespaces = ['common', 'portal'];
    const langs = Object.keys(SUPPORTED_LANGUAGES);
    
    for (const lang of langs) {
        resources[lang] = {};
        for (const ns of namespaces) {
            try {
                const response = await fetch(`locales/${lang}/${ns}.json`);
                if (response.ok) {
                    resources[lang][ns] = await response.json();
                }
            } catch (e) {
                console.warn(`Failed to load ${lang}/${ns}.json:`, e);
            }
        }
    }
}

/**
 * Initialize i18next
 */
async function initI18n() {
    await loadTranslations();
    
    const lng = detectLanguage();
    
    await i18next.init({
        lng: lng,
        fallbackLng: FALLBACK_LANGUAGE,
        defaultNS: 'portal',
        ns: ['common', 'portal'],
        resources: resources,
        interpolation: {
            escapeValue: false
        }
    });
    
    // Apply translations
    translatePage();
    
    // Build language switcher
    buildLanguageSwitcher();
    
    // Update document lang attribute
    document.documentElement.lang = lng;
    document.documentElement.dir = SUPPORTED_LANGUAGES[lng].dir;
    
    return i18next;
}

/**
 * Translate all elements with data-i18n attribute
 */
function translatePage() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const translation = i18next.t(key);
        
        // Check if it's an attribute translation (e.g., data-i18n="[title]key")
        const attrMatch = key.match(/^\[(\w+)\](.+)$/);
        if (attrMatch) {
            el.setAttribute(attrMatch[1], i18next.t(attrMatch[2]));
        } else {
            // Preserve emojis at the start of the original content
            const originalText = el.textContent;
            const emojiMatch = originalText.match(/^([\u{1F300}-\u{1F9FF}][\u{FE00}-\u{FE0F}]?\s*)/u);
            const emoji = emojiMatch ? emojiMatch[1] : '';
            
            // Check if translation starts with emoji already
            if (/^[\u{1F300}-\u{1F9FF}]/u.test(translation)) {
                el.textContent = translation;
            } else if (emoji && !translation.startsWith(emoji.trim())) {
                el.textContent = emoji + translation;
            } else {
                el.textContent = translation;
            }
        }
    });
    
    // Translate placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        el.placeholder = i18next.t(key);
    });
    
    // Translate titles
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        el.title = i18next.t(key);
    });
}

/**
 * Build the language switcher UI
 */
function buildLanguageSwitcher() {
    const container = document.getElementById('language-switcher');
    if (!container) return;
    
    container.innerHTML = '';
    
    const currentLang = i18next.language;
    
    Object.entries(SUPPORTED_LANGUAGES).forEach(([code, info]) => {
        const btn = document.createElement('button');
        btn.className = `lang-btn ${code === currentLang ? 'active' : ''}`;
        btn.setAttribute('data-lang', code);
        btn.innerHTML = `${info.flag} <span class="lang-name">${info.name}</span>`;
        btn.onclick = () => changeLanguage(code);
        container.appendChild(btn);
    });
}

/**
 * Change language
 */
async function changeLanguage(lang) {
    if (!SUPPORTED_LANGUAGES[lang]) return;
    
    localStorage.setItem(STORAGE_KEY, lang);
    await i18next.changeLanguage(lang);
    
    translatePage();
    buildLanguageSwitcher();
    
    document.documentElement.lang = lang;
    document.documentElement.dir = SUPPORTED_LANGUAGES[lang].dir;
    
    // Dispatch event for other components
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: lang } }));
}

/**
 * Format number according to current locale
 */
function formatNumber(num, options = {}) {
    const lang = i18next.language;
    return new Intl.NumberFormat(lang, options).format(num);
}

/**
 * Format date according to current locale
 */
function formatDate(date, options = {}) {
    const lang = i18next.language;
    const defaultOptions = { dateStyle: 'medium', timeStyle: 'short' };
    return new Intl.DateTimeFormat(lang, { ...defaultOptions, ...options }).format(date);
}

/**
 * Format currency according to current locale
 */
function formatCurrency(amount, currency = 'EUR') {
    const lang = i18next.language;
    return new Intl.NumberFormat(lang, { style: 'currency', currency }).format(amount);
}

// Export for use in other scripts
window.BlauweissI18n = {
    init: initI18n,
    t: (key, options) => i18next.t(key, options),
    changeLanguage,
    formatNumber,
    formatDate,
    formatCurrency,
    getCurrentLanguage: () => i18next.language,
    getSupportedLanguages: () => SUPPORTED_LANGUAGES
};
