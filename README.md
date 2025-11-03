# Slovak TV Program - Home Assistant Integrácia

Integrácia pre sťahovanie TV programu slovenských televízií do Home Assistant s týždenným programom a custom kartou pre dashboard.

## ✨ Funkcie

- 📺 Sťahovanie TV programu z RTVS XMLTV API
- 📅 Týždenný program dopredu
- 🎯 Výber kanálov: RTVS Jednotka, Dvojka, :24, Šport, TV Markíza, Doma, Dajto, JOJ, JOJ Plus, WAU, Prima, TA3
- 📊 Detailné informácie o pořadoch (názov, čas, žáner, popis, dĺžka)
- 🎨 Custom Lovelace karta s možnosťou výberu počtu dní
- 🔄 Automatická aktualizácia každých 6 hodín

## 📦 Inštalácia

### Integrácia

1. **Skopírujte zložku integrácie** do vášho Home Assistant:
   ```
   custom_components/sk_tv_program/
   ```
   Do adresára: `/config/custom_components/`

2. **Reštartujte Home Assistant**

3. **Pridajte integráciu:**
   - Choďte do **Nastavenia** → **Zariadenia a služby**
   - Kliknite na **+ Pridať integráciu**
   - Vyhľadajte "Slovak TV Program"
   - Vyberte kanály, ktoré chcete sledovať
   - Kliknite na **Odoslať**

### Custom Karta

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

3. **Pridajte kartu do dashboardu:**
   - Upravte váš dashboard
   - Kliknite **+ Add Card**
   - Vyhľadajte "TV Program Card"
   - Alebo použite manuálnu konfiguráciu (pozrite nižšie)

## 🔧 Konfigurácia Karty

### Základná konfigurácia
```yaml
type: custom:tv-program-card
entity: sensor.tv_program_rtvs1
title: TV Program RTVS Jednotka
days: 3
```

### Pokročilá konfigurácia
```yaml
type: custom:tv-program-card
entity: sensor.tv_program_markiza
title: TV Markíza Program
days: 5
show_genre: true
show_duration: true
show_description: true
max_programs: 50
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

## 🔄 Aktualizácia dát

- Dáta sa automaticky aktualizujú každých **6 hodín**
- Program je dostupný na **7 dní dopredu**
- Integráciu môžete ručne aktualizovať z karty integrácie

## 📝 Poznámky

- Integrácia používa **RTVS XMLTV API**
- API je dostupné na: http://api.rtvs.sk/xml/xmltv.xml
- Program je generovaný live z vysielacieho pracoviska
- Aktualizované každú minútu s presnosťou na sekundu

## 🐛 Riešenie problémov

### Integrácia sa nenačíta
- Skontrolujte, či je zložka `custom_components/sk_tv_program/` správne skopírovaná
- Reštartujte Home Assistant
- Skontrolujte logy v **Nastavenia** → **Systém** → **Logy**

### Karta sa nezobrazuje
- Skontrolujte, či je súbor `tv-program-card.js` v zložke `www/`
- Overte, že je karta pridaná ako resource
- Vymažte cache prehliadača (Ctrl+F5)

### Dáta sa neaktualizujú
- Skontrolujte pripojenie k internetu
- RTVS API môže byť dočasne nedostupné
- Skontrolujte logy pre chyby

## 🎯 Plánované funkcie

- [ ] Podpora ďalších TV staníc
- [ ] Filtrovanie pořadov podľa žánru
- [ ] Obľúbené pořady
- [ ] Notifikácie pred začiatkom vybraných pořadov
- [ ] Vyhľadávanie v programe

## 📄 Licencia

Tento projekt je poskytovaný "tak ako je" bez záruky.

## 🤝 Prispievanie

Príspevky sú vítané! Vytvorte issue alebo pull request.

---

**Vytvorené pre komunitu Home Assistant** 🏠
