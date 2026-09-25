#!/usr/bin/env bash
# AI Hikaye & Roman Oluşturma: becerileri kullanıcı düzeyinde kurar (git klonundan).
# Kullanım: bash betikler/kur.sh [claude|codex|opencode|hepsi]   (varsayılan: hepsi)
# Yalnızca bu paketin beceri klasörleri değiştirilir; başka beceriler korunur.
set -euo pipefail
KOK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HEDEF="${1:-hepsi}"

kur() {
  local ad="$1" klasor="$2"
  mkdir -p "$klasor"
  for beceri in "$KOK"/skills/*/; do
    local isim; isim="$(basename "$beceri")"
    if [ -L "$klasor/$isim" ]; then
      echo "Atlandı (sembolik bağlantı): $klasor/$isim"; continue
    fi
    rm -rf "${klasor:?}/$isim"
    cp -R "$beceri" "$klasor/$isim"
    find "$klasor/$isim" -name '__pycache__' -type d -prune -exec rm -rf {} +
  done
  echo "✓ $ad: $(ls -d "$KOK"/skills/*/ | wc -l | tr -d ' ') beceri → $klasor"
}

case "$HEDEF" in
  claude)   kur "Claude Code" "$HOME/.claude/skills" ;;
  codex)    kur "OpenAI Codex" "$HOME/.agents/skills" ;;
  opencode) kur "OpenCode" "${XDG_CONFIG_HOME:-$HOME/.config}/opencode/skills" ;;
  hepsi)
    kur "Claude Code" "$HOME/.claude/skills"
    kur "OpenAI Codex" "$HOME/.agents/skills"
    kur "OpenCode" "${XDG_CONFIG_HOME:-$HOME/.config}/opencode/skills" ;;
  *) echo "Bilinmeyen hedef: $HEDEF (claude|codex|opencode|hepsi)" >&2; exit 2 ;;
esac
echo "Yazım projenizde ajanları ve kancaları kurmak için ajanınızda /hikaye-kurulum çalıştırın."
