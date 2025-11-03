#!/bin/bash

# Slovak TV Program - Inštalačný skript pre Home Assistant
# ========================================================

echo "======================================"
echo "Slovak TV Program - Inštalácia"
echo "======================================"
echo ""

# Detekcia Home Assistant konfiguračného adresára
if [ -d "/config" ]; then
    HA_CONFIG="/config"
elif [ -d "$HOME/.homeassistant" ]; then
    HA_CONFIG="$HOME/.homeassistant"
else:
    echo "⚠️  Home Assistant konfiguračný adresár nebol nájdený!"
    read -p "Zadajte cestu k Home Assistant config adresáru: " HA_CONFIG
fi

echo "📁 Home Assistant config: $HA_CONFIG"
echo ""

# Vytvorenie potrebných adresárov
echo "📂 Vytváranie adresárov..."
mkdir -p "$HA_CONFIG/custom_components"
mkdir -p "$HA_CONFIG/www"

# Kontrola, či existujú zdrojové súbory
if [ ! -d "custom_components/sk_tv_program" ]; then
    echo "❌ Chyba: Zložka custom_components/sk_tv_program nebola nájdená!"
    echo "   Spustite tento skript zo zložky projektu."
    exit 1
fi

# Kopírovanie integrácie
echo "📦 Kopírovanie integrácie..."
if [ -d "$HA_CONFIG/custom_components/sk_tv_program" ]; then
    echo "⚠️  Integrácia už existuje. Prepísať? (ano/nie)"
    read -r RESPONSE
    if [ "$RESPONSE" != "ano" ] && [ "$RESPONSE" != "a" ] && [ "$RESPONSE" != "y" ] && [ "$RESPONSE" != "yes" ]; then
        echo "   Preskakujem inštaláciu integrácie..."
    else
        rm -rf "$HA_CONFIG/custom_components/sk_tv_program"
        cp -r "custom_components/sk_tv_program" "$HA_CONFIG/custom_components/"
        echo "✅ Integrácia aktualizovaná"
    fi
else
    cp -r "custom_components/sk_tv_program" "$HA_CONFIG/custom_components/"
    echo "✅ Integrácia nainštalovaná"
fi

# Kopírovanie karty
echo "🎨 Kopírovanie custom karty..."
if [ -f "$HA_CONFIG/www/tv-program-card.js" ]; then
    echo "⚠️  Karta už existuje. Prepísať? (ano/nie)"
    read -r RESPONSE
    if [ "$RESPONSE" != "ano" ] && [ "$RESPONSE" != "a" ] && [ "$RESPONSE" != "y" ] && [ "$RESPONSE" != "yes" ]; then
        echo "   Preskakujem inštaláciu karty..."
    else
        cp "www/tv-program-card.js" "$HA_CONFIG/www/"
        echo "✅ Karta aktualizovaná"
    fi
else
    cp "www/tv-program-card.js" "$HA_CONFIG/www/"
    echo "✅ Karta nainštalovaná"
fi

echo ""
echo "======================================"
echo "✨ Inštalácia dokončená!"
echo "======================================"
echo ""
echo "📝 Ďalšie kroky:"
echo ""
echo "1. Reštartujte Home Assistant"
echo ""
echo "2. Pridajte resource pre custom kartu:"
echo "   Nastavenia → Dashboardy → Resources → Add Resource"
echo "   URL: /local/tv-program-card.js"
echo "   Type: JavaScript Module"
echo ""
echo "3. Pridajte integráciu:"
echo "   Nastavenia → Zariadenia a služby → + Pridať integráciu"
echo "   Vyhľadajte: Slovak TV Program"
echo ""
echo "4. Pridajte kartu do dashboardu:"
echo "   Upraviť dashboard → + Add Card"
echo "   Vyhľadajte: TV Program Card"
echo ""
echo "📖 Pre viac informácií pozrite README.md"
echo ""
