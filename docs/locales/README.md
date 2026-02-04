# 🌍 Blauweiss Portal i18n - Translation Guide

## Supported Languages

| Code | Language | Flag | Status |
|------|----------|------|--------|
| `de` | Deutsch | 🇦🇹 | ✅ Complete |
| `en` | English | 🇺🇸 | ✅ Complete |
| `ja` | 日本語 | 🇯🇵 | ✅ Complete |
| `zh` | 中文 | 🇨🇳 | ✅ Complete |
| `th` | ไทย | 🇹🇭 | ✅ Complete |
| `ka` | ქართული | 🇬🇪 | ✅ Complete |
| `hi` | हिन्दी | 🇮🇳 | ✅ Complete |

## Adding a New Language

### Step 1: Create the locale folder

```bash
mkdir -p locales/XX  # Replace XX with ISO 639-1 code (e.g., 'ko' for Korean)
```

### Step 2: Copy English files as template

```bash
cp locales/en/common.json locales/XX/
cp locales/en/portal.json locales/XX/
```

### Step 3: Translate the JSON files

Edit both files and translate all values. Keep the keys unchanged!

```json
// locales/ko/common.json
{
    "actions": {
        "start": "시작",      // Translated
        "stop": "정지",       // Translated
        ...
    }
}
```

### Step 4: Register the language

Edit `js/i18n.js` and add your language to `SUPPORTED_LANGUAGES`:

```javascript
const SUPPORTED_LANGUAGES = {
    // ... existing languages ...
    ko: { name: '한국어', flag: '🇰🇷', dir: 'ltr' },
};
```

### Step 5: Test

Open `portal.html` in a browser and select your new language from the switcher.

## File Structure

```
locales/
├── de/                 # German (Default)
│   ├── common.json     # Shared UI elements (buttons, status, errors)
│   └── portal.json     # Portal-specific content
├── en/                 # English (Fallback)
│   ├── common.json
│   └── portal.json
└── XX/                 # Your language
    ├── common.json
    └── portal.json
```

## Translation Tips

### Namespaces

- **common**: Generic UI elements used across all pages
  - `actions`: Button labels (Start, Stop, Save, etc.)
  - `status`: Status indicators (Active, Error, Loading, etc.)
  - `errors`: Error messages
  - `navigation`: Menu items
  
- **portal**: Page-specific content
  - `header`: Page title and subtitle
  - `sections`: Section headers
  - `applications`, `crm`, `billing`, etc.: Feature-specific strings

### Placeholders

Some strings contain placeholders like `{{action}}` or `{{id}}`. Keep these exactly as-is:

```json
// ✅ Correct
"pipelineStarted": "Pipeline #{{id}} wurde gestartet!"

// ❌ Wrong - placeholder modified
"pipelineStarted": "Pipeline #{id} wurde gestartet!"
```

### Text Direction

For RTL languages (Arabic, Hebrew, etc.), set `dir: 'rtl'` in the language config:

```javascript
ar: { name: 'العربية', flag: '🇸🇦', dir: 'rtl' },
```

## Testing Checklist

- [ ] All strings translated (no English fallbacks visible)
- [ ] Placeholders work correctly (`{{action}}`, `{{id}}`, etc.)
- [ ] Numbers format correctly (1,234 vs 1.234)
- [ ] Dates format correctly
- [ ] Text fits in buttons and cards (no overflow)
- [ ] Language switcher shows native language name

## Common Issues

### Text Overflow

Some translations are longer than English. Test buttons and cards for overflow:

```css
/* If needed, add to specific elements */
.btn { white-space: nowrap; }
```

### Font Support

We use Noto Sans which supports most scripts. If your language needs a specific font, add it to the HTML:

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+YOUR_SCRIPT:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Missing Keys

If a key is missing in your translation, the English fallback is used. Check the browser console for warnings.

## Questions?

Contact: wolfram@blauweiss-edv.at
