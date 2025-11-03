class TvProgramCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._config = {};
    this._hass = null;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define an entity');
    }

    this._config = {
      entity: config.entity,
      days: config.days || 3,
      title: config.title || 'TV Program',
      show_genre: config.show_genre !== false,
      show_duration: config.show_duration !== false,
      show_description: config.show_description !== false,
      max_programs: config.max_programs || 50,
    };

    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  render() {
    if (!this._hass || !this._config.entity) return;

    const entity = this._hass.states[this._config.entity];
    if (!entity) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div class="card-content">
            <p>Entity "${this._config.entity}" not found</p>
          </div>
        </ha-card>
      `;
      return;
    }

    const allPrograms = entity.attributes.all_programs || [];
    const channelName = entity.attributes.channel || 'TV';
    
    // Filter programs by selected days
    const now = new Date();
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + this._config.days);
    
    const filteredPrograms = allPrograms
      .filter(program => {
        if (!program.date || !program.time) return false;
        const programDate = new Date(program.date + ' ' + program.time);
        return programDate >= now && programDate <= endDate;
      })
      .slice(0, this._config.max_programs);

    const currentProgram = {
      title: entity.attributes.current_title || '',
      time: entity.attributes.current_time || '',
      genre: entity.attributes.current_genre || '',
      duration: entity.attributes.current_duration || '',
      description: entity.attributes.current_description || '',
    };

    this.shadowRoot.innerHTML = `
      <style>
        ha-card {
          padding: 16px;
        }
        .card-header {
          font-size: 24px;
          font-weight: 500;
          padding-bottom: 16px;
          border-bottom: 1px solid var(--divider-color);
        }
        .current-program {
          background: var(--primary-color);
          color: var(--text-primary-color);
          padding: 12px;
          border-radius: 8px;
          margin: 16px 0;
        }
        .current-program .title {
          font-size: 18px;
          font-weight: 500;
          margin-bottom: 8px;
        }
        .current-program .info {
          font-size: 14px;
          opacity: 0.9;
        }
        .days-selector {
          display: flex;
          gap: 8px;
          margin: 16px 0;
          flex-wrap: wrap;
        }
        .day-button {
          padding: 8px 16px;
          border: 1px solid var(--divider-color);
          border-radius: 4px;
          background: var(--card-background-color);
          cursor: pointer;
          transition: all 0.3s;
        }
        .day-button:hover {
          background: var(--primary-color);
          color: var(--text-primary-color);
        }
        .day-button.active {
          background: var(--primary-color);
          color: var(--text-primary-color);
          border-color: var(--primary-color);
        }
        .program-list {
          margin-top: 16px;
        }
        .program-item {
          padding: 12px;
          border-bottom: 1px solid var(--divider-color);
          display: flex;
          gap: 12px;
        }
        .program-item:hover {
          background: var(--secondary-background-color);
        }
        .program-time {
          font-weight: 500;
          min-width: 60px;
          color: var(--primary-text-color);
        }
        .program-details {
          flex: 1;
        }
        .program-title {
          font-weight: 500;
          margin-bottom: 4px;
        }
        .program-badge {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 12px;
          margin-right: 4px;
          background: var(--primary-color);
          color: var(--text-primary-color);
        }
        .program-info {
          font-size: 14px;
          color: var(--secondary-text-color);
          margin-top: 4px;
        }
        .program-description {
          font-size: 13px;
          color: var(--secondary-text-color);
          margin-top: 8px;
          line-height: 1.4;
        }
        .date-separator {
          font-weight: 500;
          padding: 12px 8px;
          background: var(--secondary-background-color);
          margin-top: 8px;
          border-radius: 4px;
        }
        .no-programs {
          padding: 20px;
          text-align: center;
          color: var(--secondary-text-color);
        }
      </style>
      
      <ha-card>
        <div class="card-header">
          ${this._config.title} - ${channelName}
        </div>
        
        ${currentProgram.title ? `
          <div class="current-program">
            <div class="title">▶ Nyní: ${this.escapeHtml(currentProgram.title)}</div>
            <div class="info">
              ${currentProgram.time} 
              ${this._config.show_genre && currentProgram.genre ? `• ${this.escapeHtml(currentProgram.genre)}` : ''}
              ${this._config.show_duration && currentProgram.duration ? `• ${currentProgram.duration}` : ''}
            </div>
          </div>
        ` : ''}
        
        <div class="days-selector">
          ${[1, 2, 3, 5, 7].map(days => `
            <button class="day-button ${this._config.days === days ? 'active' : ''}" 
                    onclick="this.getRootNode().host.updateDays(${days})">
              ${days} ${days === 1 ? 'den' : days < 5 ? 'dny' : 'dní'}
            </button>
          `).join('')}
        </div>
        
        <div class="program-list">
          ${filteredPrograms.length > 0 ? this.renderPrograms(filteredPrograms) : `
            <div class="no-programs">Žádné nadcházející pořady</div>
          `}
        </div>
      </ha-card>
    `;
  }

  renderPrograms(programs) {
    let html = '';
    let lastDate = '';

    programs.forEach(program => {
      // Add date separator if date changes
      if (program.date !== lastDate) {
        const date = new Date(program.date);
        const dateStr = this.formatDate(date);
        html += `<div class="date-separator">${dateStr}</div>`;
        lastDate = program.date;
      }

      html += `
        <div class="program-item">
          <div class="program-time">${program.time || ''}</div>
          <div class="program-details">
            <div class="program-title">
              ${program.supertitle ? `${this.escapeHtml(program.supertitle)}: ` : ''}
              ${this.escapeHtml(program.title || 'Neznámý pořad')}
              ${program.episode_title ? ` - ${this.escapeHtml(program.episode_title)}` : ''}
            </div>
            ${program.live || program.premiere || program.episode ? `
              <div>
                ${program.live ? '<span class="program-badge">ŽIVĚ</span>' : ''}
                ${program.premiere ? '<span class="program-badge">PREMIÉRA</span>' : ''}
                ${program.episode ? `<span class="program-badge">${this.escapeHtml(program.episode)}</span>` : ''}
              </div>
            ` : ''}
            ${this._config.show_genre || this._config.show_duration ? `
              <div class="program-info">
                ${this._config.show_genre && program.genre ? this.escapeHtml(program.genre) : ''}
                ${this._config.show_genre && program.genre && this._config.show_duration && program.duration ? ' • ' : ''}
                ${this._config.show_duration && program.duration ? program.duration : ''}
              </div>
            ` : ''}
            ${this._config.show_description && program.description ? `
              <div class="program-description">${this.escapeHtml(program.description)}</div>
            ` : ''}
          </div>
        </div>
      `;
    });

    return html;
  }

  formatDate(date) {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Dnes';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Zítra';
    } else {
      const days = ['Neděle', 'Pondělí', 'Úterý', 'Středa', 'Čtvrtek', 'Pátek', 'Sobota'];
      return `${days[date.getDay()]} ${date.getDate()}.${date.getMonth() + 1}.`;
    }
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  updateDays(days) {
    this._config.days = days;
    this.render();
  }

  getCardSize() {
    return 3;
  }
}

customElements.define('tv-program-card', TvProgramCard);

// Register the card
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'tv-program-card',
  name: 'TV Program Card',
  description: 'Karta pro zobrazení TV programu z České televize',
  preview: true,
});

// Add to card picker
console.info(
  '%c TV-PROGRAM-CARD %c Version 1.0.0 ',
  'color: orange; font-weight: bold; background: black',
  'color: white; font-weight: bold; background: dimgray',
);
