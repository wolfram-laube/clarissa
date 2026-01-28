# 🔍 Advanced Search

<div id="pagefind-search"></div>

<link href="/_pagefind/pagefind-ui.css" rel="stylesheet">
<style>
  :root {
    --pagefind-ui-scale: 1;
    --pagefind-ui-primary: #7c4dff;
    --pagefind-ui-text: #ddd;
    --pagefind-ui-background: #1e1e2e;
    --pagefind-ui-border: #555;
    --pagefind-ui-tag: #7c4dff;
    --pagefind-ui-border-width: 2px;
    --pagefind-ui-border-radius: 8px;
  }
  .pagefind-ui .pagefind-ui__search-input {
    background: #2d2d3d !important;
    color: #fff !important;
    font-size: 1.1rem !important;
  }
  .pagefind-ui .pagefind-ui__result-link {
    color: #bb86fc !important;
  }
  .pagefind-ui .pagefind-ui__result-excerpt {
    color: #ccc !important;
  }
  #pagefind-search {
    margin: 2rem 0;
  }
</style>
<script src="/_pagefind/pagefind-ui.js"></script>
<script>
  window.addEventListener('DOMContentLoaded', () => {
    new PagefindUI({
      element: "#pagefind-search",
      showSubResults: true,
      showImages: false,
      translations: {
        placeholder: "Suche / Search (EN + DE)...",
        zero_results: "Keine Ergebnisse für '[SEARCH_TERM]' / No results"
      }
    });
  });
</script>

---

!!! tip "Multilingual Search"
    This search finds content in **both English and German**.
    
    Try: `permeability`, `Permeabilität`, `simulation`, `Reservoir`

!!! info "Quick Search"
    For basic search, press `/` anywhere on the site.
