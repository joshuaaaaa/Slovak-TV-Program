# Slovak TV Program - Home Assistant Integrácia

Integrácia pre sťahovanie TV programu slovenských televízií do Home Assistant s týždenným programom a custom kartou pre dashboard.

## ✨ Funkcie

- 📺 Sťahovanie TV programu z open-epg.com
- 📅 Týždenný program dopredu
- 🎯 Výber kanálov: RTVS Jednotka, Dvojka, :24, Šport, TV Markíza, Doma, Dajto, JOJ, JOJ Plus, WAU, Prima, TA3
- 📊 Detailné informácie o pořadoch (názov, čas, žáner, popis, dĺžka)
- 🎨 Custom Lovelace karta s možnosťou výberu počtu dní
- 🔄 Automatická aktualizácia každých 6 hodín

## 📦 Inštalácia

### Metóda 1: HACS (Odporúčaná)

1. **Otvorte HACS** v Home Assistant
2. Kliknite na **Integrations**
3. Kliknite na **⋮** (tri bodky v pravom hornom rohu)
4. Vyberte **Custom repositories**
5. Pridajte URL repozitára:
```
  https://github.com/joshuaaaaa/Slovak-TV-Program
```
6. Vyberte kategóriu: **Integration**
7. Kliknite **Add**
8. Nájdite **Slovak TV Program** v zozname integrácií
9. Kliknite **Download**
10. **Reštartujte Home Assistant**


### Metóda 2: Manuálna inštalácia

#### Integrácia

1. **Skopírujte zložku integrácie** do vášho Home Assistant:
```
   custom_components/sk_tv_program/
```
   Do adresára: `/config/custom_components/`

2. **Reštartujte Home Assistant**

#### Custom Karta

1. **Skopírujte súbor karty:**
```
   www/tv-program-card.js
```
   Do adresára: `/config/www/`

2. **Pridajte kartu ako resource** v Lovelace:
   - Choďte do **Nastavenia** → **Dashboardy**
   - Kliknite na tri bodky → **Resources**
   - Kliknite **+ Add Resource**
   - URL: `/local/tv-program-card.js`
   - Resource type: **JavaScript Module**
   - Kliknite **Create**

## ⚙️ Konfigurácia Integrácie

1. **Pridajte integráciu:**
   - Choďte do **Nastavenia** → **Zariadenia a služby**
   - Kliknite na **+ Pridať integráciu**
   - Vyhľadajte "Slovak TV Program"
   - Vyberte kanály, ktoré chcete sledovať
   - Kliknite na **Odoslať**

2. **Upravte integráciu** (voliteľné):
   - V zozname integrácií kliknite na **Slovak TV Program**
   - Kliknite na **Configure**
   - Zmeňte výber kanálov podľa potreby

## 🔧 Konfigurácia Karty

### Základná konfigurácia
```yaml
type: custom:tv-program-card
entity: sensor.tv_program_rtvs_dvojka
title: TV Program RTVS Jednotka
days: 3
```

### Pokročilá konfigurácia
```yaml
type: custom:tv-program-card
entity: sensor.tv_program_wau
title: TV WAU Program
days: 5
show_genre: true
show_duration: true
show_description: true
max_programs: 50
```

### Viac kanálov na jednom dashboarde
```yaml
type: vertical-stack
cards:
  - type: custom:tv-program-card
    entity: sensor.tv_program_rtvs1
    title: RTVS Jednotka
    days: 1
    max_programs: 10
  
  - type: custom:tv-program-card
    entity: sensor.tv_program_markiza
    title: TV Markíza
    days: 1
    max_programs: 10
  
  - type: custom:tv-program-card
    entity: sensor.tv_program_joj
    title: TV JOJ
    days: 1
    max_programs: 10
```

### Parametre karty

| Parameter | Typ | Predvolené | Popis |
|----------|-----|---------|-------|
| `entity` | string | **povinné** | Entity ID TV program senzora |
| `title` | string | "TV Program" | Nadpis karty |
| `days` | number | 3 | Počet dní programu na zobrazenie (1-7) |
| `show_genre` | boolean | true | Zobraziť žáner pořadu |
| `show_duration` | boolean | true | Zobraziť dĺžku pořadu |
| `show_description` | boolean | true | Zobraziť popis pořadu |
| `max_programs` | number | 50 | Maximálny počet zobrazených pořadov |

## 📱 Použitie

### Dostupné senzory
Po inštalácii budú vytvorené senzory pre každý vybraný kanál:
- `sensor.tv_program_rtvs1` - RTVS Jednotka
- `sensor.tv_program_rtvs2` - RTVS Dvojka
- `sensor.tv_program_rtvs24` - RTVS :24
- `sensor.tv_program_rtvs_sport` - RTVS Šport
- `sensor.tv_program_markiza` - TV Markíza
- `sensor.tv_program_doma` - TV Doma
- `sensor.tv_program_dajto` - TV Dajto
- `sensor.tv_program_joj` - TV JOJ
- `sensor.tv_program_joj_plus` - JOJ Plus
- `sensor.tv_program_wau` - WAU
- `sensor.tv_program_prima` - TV Prima
- `sensor.tv_program_ta3` - TA3

### Atribúty senzora
Každý senzor obsahuje nasledujúce atribúty:

- **current_*** - informácie o aktuálnom pořade
- **upcoming_programs** - zoznam nadchádzajúcich 10 pořadov
- **all_programs** - kompletný týždenný program

### Príklad použitia v automatizácii

#### Upozornenie na začiatok obľúbeného pořadu
```yaml
automation:
  - alias: "Upozornenie na obľúbený pořad"
    trigger:
      - platform: state
        entity_id: sensor.tv_program_rtvs1
    condition:
      - condition: template
        value_template: "{{ 'Správy' in state_attr('sensor.tv_program_rtvs1', 'current_title') }}"
    action:
      - service: notify.mobile_app
        data:
          message: "Začínajú Správy na RTVS Jednotka!"
```

#### Zapnutie TV 5 minút pred obľúbeným pořadom
```yaml
automation:
  - alias: "Zapni TV pred filmom"
    trigger:
      - platform: time_pattern
        minutes: "/1"
    condition:
      - condition: template
        value_template: >
          {% set upcoming = state_attr('sensor.tv_program_rtvs1', 'upcoming_programs') %}
          {% if upcoming and upcoming|length > 0 %}
            {% set next_program = upcoming[0] %}
            {% set now = now() %}
            {% set program_time = strptime(next_program.date ~ ' ' ~ next_program.time, '%Y-%m-%d %H:%M') %}
            {% set time_diff = (program_time - now).total_seconds() / 60 %}
            {{ time_diff <= 5 and time_diff > 4 and 'Film' in next_program.title }}
          {% else %}
            false
          {% endif %}
    action:
      - service: media_player.turn_on
        target:
          entity_id: media_player.tv_obyvacka
```

#### Denné upozornenie na večerné správy
```yaml
automation:
  - alias: "Pripomienka večerných správ"
    trigger:
      - platform: time
        at: "19:25:00"
    action:
      - service: notify.mobile_app
        data:
          title: "TV Program"
          message: >
            O 5 minút začínajú Správy na RTVS Jednotka.
            Aktuálne ide: {{ state_attr('sensor.tv_program_rtvs1', 'current_title') }}
```

## 🔄 Aktualizácia dát

- Dáta sa automaticky aktualizujú každých **6 hodín**
- Program je dostupný na **7 dní dopredu**
- Integráciu môžete ručne aktualizovať z karty integrácie (tri bodky → Reload)

## 📝 Poznámky

- Integrácia používa **open-epg.com** ako zdroj EPG dát
- API je dostupné na: https://www.open-epg.com/files/slovakia1.xml
- Dáta sú aktualizované denne
- Pokrytie: všetky hlavné slovenské TV stanice

## 🐛 Riešenie problémov

### Integrácia sa nenačíta
- Skontrolujte, či je zložka `custom_components/sk_tv_program/` správne skopírovaná
- Reštartujte Home Assistant
- Skontrolujte logy v **Nastavenia** → **Systém** → **Logy**
- Hľadajte chyby obsahujúce `sk_tv_program`

### Karta sa nezobrazuje
- Skontrolujte, či je súbor `tv-program-card.js` v zložke `www/`
- Overte, že je karta pridaná ako resource
- Vymažte cache prehliadača (Ctrl+F5 alebo Cmd+Shift+R)
- Skontrolujte konzolu prehliadača (F12) pre JavaScript chyby

### Senzory nemajú žiadne dáta
- Počkajte 5-10 minút po prvej inštalácii
- Skontrolujte pripojenie k internetu
- Overte dostupnosť https://www.open-epg.com/files/slovakia1.xml
- Skontrolujte logy pre chyby API
- Skúste manuálne aktualizovať integráciu

### Senzory zobrazujú "Nedostupné"
- Program pre daný kanál môže byť dočasne nedostupný v EPG
- Skúste vybrať iný kanál na otestovanie
- Reštartujte integráciu

### Aktualizácia cez HACS
1. Otvorte HACS → Integrations
2. Nájdite **Slovak TV Program**
3. Ak je dostupná aktualizácia, kliknite **Update**
4. Reštartujte Home Assistant

## 🎯 Plánované funkcie

- [ ] Podpora ďalších TV staníc
- [ ] Filtrovanie pořadov podľa žánru
- [ ] Obľúbené pořady s notifikáciami
- [ ] Vyhľadávanie v programe
- [ ] Export programu do kalendára
- [ ] Integrácia s media_player entitami



## 📄 Licencia

MIT License - pozrite súbor [LICENSE](LICENSE) pre detaily.



## ⭐ Podpora projektu

Ak sa vám táto integrácia páči, dajte hviezdu na GitHube! ⭐

## http://buymeacoffee.com/jakubhruby


<img width="150" height="150" alt="qr-code" src="https://github.com/user-attachments/assets/2581bf36-7f7d-4745-b792-d1abaca6e57d" />

---

**Vytvorené pre komunitu Home Assistant** 🏠

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/vase-uzivatelske-meno/sk_tv_program.svg)](https://github.com/vase-uzivatelske-meno/sk_tv_program/releases)
[![License](https://img.shields.io/github/license/vase-uzivatelske-meno/sk_tv_program.svg)](LICENSE)
