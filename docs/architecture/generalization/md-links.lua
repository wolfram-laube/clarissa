-- Wandelt relative Links auf .md-Dateien in Links auf die Webseite um.
-- Erwartet die Metadaten-Variable site-base (URL des Ordners, mit / am Ende).
local base

local function Meta(m)
  if m["site-base"] then
    base = pandoc.utils.stringify(m["site-base"])
  end
end

local function Link(el)
  local t = el.target
  if not base or t:match("^%a+:") or t:sub(1, 1) == "#" then
    return nil
  end
  local path, frag = t:match("^([^#]*)(#?.*)$")
  if not path:match("%.md$") then
    return nil
  end
  path = path:gsub("index%.md$", ""):gsub("%.md$", "/")
  local b = base
  while path:sub(1, 3) == "../" do
    b = b:gsub("[^/]+/$", "")
    path = path:sub(4)
  end
  el.target = b .. path .. frag
  return el
end

return { { Meta = Meta }, { Link = Link } }
