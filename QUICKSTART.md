# 🚀 Rýchly štart - Slovak TV Program

## 📥 Stiahnutie a inštalácia

1. **Stiahnite ZIP súbor** `sk_tv_program.zip`
2. **Rozbaľte** obsah archívu
3. **Spustite inštaláciu**

---

## 📁 Manuálna inštalácia

### Krok 1: Skopírujte integráciu
```
sk_tv_program/custom_components/sk_tv_program/
    ↓ skopírovať do ↓
/config/custom_components/sk_tv_program/
```

### Krok 2: Skopírujte kartu
```
sk_tv_program/www/tv-program-card.js
    ↓ skopírovať do ↓
/config/www/tv-program-card.js
```

### Krok 3: Reštartujte Home Assistant
- **Nastavenia** → **Systém** → **Reštartovať**

---

## 🎨 Konfigurácia

### 1. Pridajte integráciu
1. **Nastavenia** → **Zariadenia a služby**
2. Kliknite **+ Pridať integráciu**
3. Vyhľadajte **"Slovak TV Program"**
4. Vyberte TV kanály:
   - ✅ RTVS Jednotka
   - ✅ RTVS Dvojka
   - ✅ RTVS :24
   - ✅ RTVS Šport
   - ✅ TV Markíza
   - ✅ TV Doma
   - ✅ TV Dajto
   - ✅ TV JOJ
   - ✅ JOJ Plus
   - ✅ WAU
   - ✅ TV Prima
   - ✅ TA3
5. Kliknite **Odoslať**

### 2. Pridajte kartu ako resource
1. **Nastavenia** → **Dashboardy**
2. Kliknite na **⋮** (tri bodky) → **Resources**
3. Kliknite **+ Add Resource**
4. Vyplňte:
   - **URL:** `/local/tv-program-card.js`
   - **Resource type:** `JavaScript Module`
5. Kliknite **Create**
6. **Obnovte stránku** (Ctrl+F5 alebo Cmd+R)

### 3. Pridajte kartu do dashboardu
```yaml
type: custom:tv-program-card
entity: sensor.tv_program_rtvs1
title: Program RTVS Jednotka
days: 3
```

---

## ✅ Kontrola funkčnosti

### Senzory (automaticky vytvorené)
- `sensor.tv_program_rtvs1`
- `sensor.tv_program_rtvs2`
- `sensor.tv_program_markiza`
- atď.

---

## 🐛 Riešenie problémov

### ❌ Karta sa nezobrazuje
**Riešenie:**
1. Skontrolujte, že je súbor `tv-program-card.js` v zložke `/config/www/`
2. Overte, že je resource pridaný v dashboarde
3. Obnovte stránku s vymazaním cache: **Ctrl+F5** (Windows) alebo **Cmd+Shift+R** (Mac)

### ❌ Integrácia sa nenačíta
**Riešenie:**
1. Overte, že zložka je správne umiestnená:
   `/config/custom_components/sk_tv_program/`
2. Reštartujte Home Assistant
3. Skontrolujte logy: **Nastavenia** → **Systém** → **Logy**

---

**Užite si sledovanie TV programu! 📺✨**
