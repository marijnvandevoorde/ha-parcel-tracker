const CARRIERS = {
  auto: 'Auto-detect',
  bpost: 'bPost',
  dhl: 'DHL (Internationaal)',
  dhl_de: 'DHL Germany',
  dpd: 'DPD',
  fourpx: '4PX / China Post',
  tnt: 'TNT / FedEx',
  ups: 'UPS',
  postnl: 'PostNL',
  colisprive: 'Colis Privé (experimenteel)',
  gls: 'GLS (via pkge.net)',
  mondialrelay: 'Mondial Relay (via pkge.net)',
};

const STATUS_COLORS = {
  delivered:        '#4CAF50',
  in_transit:       '#2196F3',
  out_for_delivery: '#FF9800',
  pending:          '#9E9E9E',
  exception:        '#F44336',
  unknown:          '#9E9E9E',
  empty:            'transparent',
};

const TRANSLATIONS = {
  nl: {
    last_checked:     'Laatste controle',
    never_checked:    'Nog niet gecontroleerd',
    loading:          'Laden…',
    refresh:          '↻ Ververs',
    refreshing:       'Bezig…',
    active_parcels:   'Actieve pakketten',
    no_parcels:       'Nog geen pakketten toegevoegd.',
    no_parcels_hint:  'Klik hieronder om je eerste pakket in te voeren.',
    max_reached:      'Maximum van 10 pakketten bereikt.',
    add_parcel:       'Pakket toevoegen',
    edit_parcel:      'Pakket bewerken',
    new_parcel:       'Nieuw pakket toevoegen',
    name_label:       'Naam (optioneel)',
    name_placeholder: 'bijv. Bestelling bol.com',
    tracking_label:   'Trackingnummer',
    tracking_placeholder: 'bijv. JD014600004860246190',
    carrier_label:    'Bezorgdienst',
    save:             'Opslaan',
    saving:           'Opslaan…',
    cancel:           'Annuleren',
    edit:             'Bewerken',
    delete:           'Verwijderen',
    track_link:       'Volg pakket →',
    confirm_delete:   'Pakket verwijderen?',
    saved:            'Pakket opgeslagen!',
    deleted:          'Pakket verwijderd.',
    save_error:       'Opslaan mislukt. Probeer opnieuw.',
    load_error:       'Kon pakketdata niet laden. Controleer of de integratie actief is.',
    refresh_error:    'Vernieuwen mislukt. Probeer opnieuw.',
    check_logs:       'Controleer de HA-logs voor meer info',
    just_now:         '< 1 min geleden',
    min_ago:          'min geleden',
    status: {
      delivered:        'Bezorgd',
      in_transit:       'Onderweg',
      out_for_delivery: 'Wordt vandaag bezorgd',
      pending:          'Aangemeld',
      exception:        'Probleem',
      unknown:          'Onbekend',
      empty:            '',
    },
  },
  fr: {
    last_checked:     'Dernière vérification',
    never_checked:    'Pas encore vérifié',
    loading:          'Chargement…',
    refresh:          '↻ Actualiser',
    refreshing:       'En cours…',
    active_parcels:   'Colis actifs',
    no_parcels:       'Aucun colis ajouté.',
    no_parcels_hint:  'Cliquez ci-dessous pour ajouter votre premier colis.',
    max_reached:      'Maximum de 10 colis atteint.',
    add_parcel:       'Ajouter un colis',
    edit_parcel:      'Modifier le colis',
    new_parcel:       'Ajouter un nouveau colis',
    name_label:       'Nom (optionnel)',
    name_placeholder: 'ex. Commande Amazon',
    tracking_label:   'Numéro de suivi',
    tracking_placeholder: 'ex. JD014600004860246190',
    carrier_label:    'Transporteur',
    save:             'Enregistrer',
    saving:           'Enregistrement…',
    cancel:           'Annuler',
    edit:             'Modifier',
    delete:           'Supprimer',
    track_link:       'Suivre le colis →',
    confirm_delete:   'Supprimer ce colis ?',
    saved:            'Colis enregistré !',
    deleted:          'Colis supprimé.',
    save_error:       'Échec de l\'enregistrement. Réessayez.',
    load_error:       'Impossible de charger les données. Vérifiez que l\'intégration est active.',
    refresh_error:    'Échec de l\'actualisation. Réessayez.',
    check_logs:       'Consultez les logs HA pour plus d\'informations',
    just_now:         '< 1 min',
    min_ago:          'min',
    status: {
      delivered:        'Livré',
      in_transit:       'En transit',
      out_for_delivery: 'En cours de livraison',
      pending:          'Enregistré',
      exception:        'Problème',
      unknown:          'Inconnu',
      empty:            '',
    },
  },
  en: {
    last_checked:     'Last checked',
    never_checked:    'Not yet checked',
    loading:          'Loading…',
    refresh:          '↻ Refresh',
    refreshing:       'Refreshing…',
    active_parcels:   'Active parcels',
    no_parcels:       'No parcels added yet.',
    no_parcels_hint:  'Click below to add your first parcel.',
    max_reached:      'Maximum of 10 parcels reached.',
    add_parcel:       'Add parcel',
    edit_parcel:      'Edit parcel',
    new_parcel:       'Add new parcel',
    name_label:       'Name (optional)',
    name_placeholder: 'e.g. Amazon order',
    tracking_label:   'Tracking number',
    tracking_placeholder: 'e.g. JD014600004860246190',
    carrier_label:    'Carrier',
    save:             'Save',
    saving:           'Saving…',
    cancel:           'Cancel',
    edit:             'Edit',
    delete:           'Delete',
    track_link:       'Track parcel →',
    confirm_delete:   'Delete this parcel?',
    saved:            'Parcel saved!',
    deleted:          'Parcel deleted.',
    save_error:       'Save failed. Please try again.',
    load_error:       'Could not load parcel data. Check that the integration is active.',
    refresh_error:    'Refresh failed. Please try again.',
    check_logs:       'Check the HA logs for more information',
    just_now:         '< 1 min ago',
    min_ago:          'min ago',
    status: {
      delivered:        'Delivered',
      in_transit:       'In transit',
      out_for_delivery: 'Out for delivery',
      pending:          'Registered',
      exception:        'Exception',
      unknown:          'Unknown',
      empty:            '',
    },
  },
};

const CSS = `
  :host { display: block; }
  .container { max-width: 800px; margin: 0 auto; padding: 16px; }
  h1 {
    font-size: 1.5rem; font-weight: 400;
    color: var(--primary-text-color);
    margin: 0 0 16px 0;
    display: flex; align-items: center; gap: 10px;
  }
  .card {
    background: var(--card-background-color, #fff);
    border-radius: 12px; padding: 16px; margin-bottom: 12px;
    box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0,0,0,0.1));
  }
  .card.editing { border: 2px solid var(--primary-color); }
  .slot-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
  .slot-name { font-weight: 500; color: var(--primary-text-color); flex: 1; font-size: 1rem; }
  .badge {
    padding: 3px 10px; border-radius: 12px;
    font-size: 0.75rem; font-weight: 600; color: #fff;
    white-space: nowrap;
  }
  .tracking-num {
    font-family: monospace; font-size: 0.85rem;
    color: var(--secondary-text-color); margin-bottom: 2px;
  }
  .carrier-label { font-size: 0.8rem; color: var(--secondary-text-color); }
  .detail { font-size: 0.8rem; color: var(--secondary-text-color); margin-top: 4px; font-style: italic; }
  .detail-warn { color: var(--warning-color, #FF9800); font-style: normal; }
  a { color: var(--primary-color); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .actions { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
  button {
    border: none; border-radius: 6px; padding: 7px 14px;
    cursor: pointer; font-size: 0.875rem; font-weight: 500;
    transition: opacity 0.15s;
  }
  button:hover { opacity: 0.85; }
  button:disabled { opacity: 0.4; cursor: default; }
  .btn-primary { background: var(--primary-color); color: #fff; }
  .btn-secondary { background: var(--secondary-background-color, #eee); color: var(--primary-text-color); }
  .btn-danger { background: var(--error-color, #f44336); color: #fff; }
  .btn-sm { padding: 4px 10px; font-size: 0.8rem; }
  label {
    display: block; font-size: 0.8rem;
    color: var(--secondary-text-color); margin: 10px 0 4px;
  }
  input, select {
    width: 100%; box-sizing: border-box;
    padding: 9px 11px;
    border: 1px solid var(--divider-color, #e0e0e0);
    border-radius: 6px;
    background: var(--primary-background-color, #fff);
    color: var(--primary-text-color);
    font-size: 0.9rem;
  }
  input:focus, select:focus { outline: none; border-color: var(--primary-color); }
  .add-card {
    border: 2px dashed var(--divider-color, #ccc);
    border-radius: 12px; padding: 20px; margin-bottom: 12px;
    text-align: center; color: var(--secondary-text-color);
    cursor: pointer; transition: border-color 0.15s, color 0.15s;
  }
  .add-card:hover { border-color: var(--primary-color); color: var(--primary-color); }
  .add-icon { font-size: 1.8rem; line-height: 1; }
  .add-label { margin-top: 4px; font-size: 0.9rem; }
  .toast {
    padding: 10px 14px; border-radius: 8px; margin-bottom: 12px; font-size: 0.875rem;
  }
  .toast.success { background: #e8f5e9; color: #2e7d32; }
  .toast.error   { background: #ffebee; color: #c62828; }
  .loading { text-align: center; padding: 40px; color: var(--secondary-text-color); }
  .toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .section-label {
    font-size: 0.75rem; font-weight: 700; letter-spacing: 0.05em;
    text-transform: uppercase; color: var(--secondary-text-color);
    margin: 20px 0 8px;
  }
  .empty-state {
    text-align: center; padding: 40px 16px; color: var(--secondary-text-color);
  }
  .empty-state .big { font-size: 3rem; }
`;

class ParcelTrackerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._parcels = [];
    this._entryId = null;
    this._lastChecked = null;
    this._editing = null;
    this._loading = true;
    this._refreshing = false;
    this._saving = false;
    this._toast = null;
  }

  connectedCallback() {
    this._render();
  }

  set hass(hass) {
    const isFirst = !this._hass;
    this._hass = hass;
    if (isFirst) this._loadData();
  }

  get _t() {
    const lang = (this._hass?.language || 'en').split('-')[0];
    return TRANSLATIONS[lang] || TRANSLATIONS.en;
  }

  async _refresh() {
    if (this._refreshing || !this._entryId) return;
    this._refreshing = true;
    this._render();
    try {
      await this._hass.callWS({ type: 'parcel_tracker/refresh', entry_id: this._entryId });
    } catch (e) {
      this._showToast('error', this._t.refresh_error);
    }
    await this._loadData();
    this._refreshing = false;
    this._render();
  }

  async _loadData() {
    this._loading = true;
    this._render();
    try {
      const result = await this._hass.callWS({ type: 'parcel_tracker/list' });
      if (result && result.length > 0) {
        this._entryId = result[0].entry_id;
        this._parcels = result[0].parcels;
        this._lastChecked = result[0].last_checked ? new Date(result[0].last_checked) : null;
      }
    } catch (e) {
      this._showToast('error', this._t.load_error);
    }
    this._loading = false;
    this._render();
  }

  async _save(slot, tracking, carrier, name) {
    this._saving = true;
    this._render();
    try {
      await this._hass.callWS({
        type: 'parcel_tracker/set_parcel',
        entry_id: this._entryId,
        slot,
        tracking: tracking.trim(),
        carrier,
        friendly_name: name.trim() || `Parcel ${slot}`,
      });
      this._editing = null;
      this._showToast('success', tracking.trim() ? this._t.saved : this._t.deleted);
      await this._loadData();
    } catch (e) {
      this._showToast('error', this._t.save_error);
    }
    this._saving = false;
    this._render();
  }

  _showToast(type, text) {
    this._toast = { type, text };
    clearTimeout(this._toastTimer);
    this._toastTimer = setTimeout(() => { this._toast = null; this._render(); }, 4000);
  }

  _render() {
    const root = this.shadowRoot;
    root.innerHTML = `<style>${CSS}</style><div class="container">${this._renderBody()}</div>`;
    this._bindEvents();
  }

  _renderBody() {
    const t = this._t;
    if (this._loading) {
      return `<h1>📦 Parcel Tracker</h1><div class="loading">${t.loading}</div>`;
    }
    const active = this._parcels.filter(p => p.tracking);
    const nextEmpty = this._parcels.find(p => !p.tracking);

    return `
      <div class="toolbar">
        <h1>📦 Parcel Tracker</h1>
        <div style="display:flex;align-items:center;gap:10px">
          <span style="font-size:0.75rem;color:var(--secondary-text-color)">
            ${t.last_checked}: ${this._lastChecked ? this._formatTime(this._lastChecked) : t.never_checked}
          </span>
          <button class="btn-secondary btn-sm" id="btn-refresh" ${this._refreshing ? 'disabled' : ''}>
            ${this._refreshing ? t.refreshing : t.refresh}
          </button>
        </div>
      </div>
      ${this._toast ? `<div class="toast ${this._toast.type}">${this._esc(this._toast.text)}</div>` : ''}
      ${active.length === 0 && this._editing === null ? this._renderEmptyState() : ''}
      ${active.length > 0 ? `<div class="section-label">${t.active_parcels}</div>` : ''}
      ${active.map(p => this._editing === p.slot ? this._renderForm(p) : this._renderParcel(p)).join('')}
      ${nextEmpty
        ? (this._editing === nextEmpty.slot
            ? this._renderForm(nextEmpty)
            : this._renderAddButton(nextEmpty))
        : `<div style="font-size:0.8rem;color:var(--secondary-text-color);text-align:center">${t.max_reached}</div>`
      }
    `;
  }

  _renderEmptyState() {
    const t = this._t;
    return `
      <div class="empty-state">
        <div class="big">📦</div>
        <div style="margin-top:8px">${t.no_parcels}</div>
        <div style="font-size:0.8rem;margin-top:4px">${t.no_parcels_hint}</div>
      </div>
    `;
  }

  _renderParcel(p) {
    const t = this._t;
    const statusLabel = t.status[p.status] || '';
    const statusColor = STATUS_COLORS[p.status] || STATUS_COLORS.unknown;
    const carrierLabel = CARRIERS[p.carrier] || p.carrier;
    return `
      <div class="card" data-slot="${p.slot}">
        <div class="slot-header">
          <span class="slot-name">${this._esc(p.friendly_name)}</span>
          ${statusLabel ? `<span class="badge" style="background:${statusColor}">${statusLabel}</span>` : ''}
        </div>
        <div class="tracking-num">${this._esc(p.tracking)}</div>
        <div class="carrier-label">
          ${this._esc(carrierLabel)}
          ${p.tracking_url && p.tracking_url.startsWith('https://') ? ` &middot; <a href="${this._esc(p.tracking_url)}" target="_blank">${t.track_link}</a>` : ''}
        </div>
        ${p.status_detail
            ? `<div class="detail${(p.status === 'unknown' || p.status === 'exception') ? ' detail-warn' : ''}">${this._esc(p.status_detail)}</div>`
            : (p.status === 'unknown' ? `<div class="detail detail-warn">${t.check_logs}</div>` : '')
        }
        <div class="actions">
          <button class="btn-secondary btn-sm" data-action="edit" data-slot="${p.slot}">${t.edit}</button>
          <button class="btn-danger btn-sm" data-action="delete" data-slot="${p.slot}">${t.delete}</button>
        </div>
      </div>
    `;
  }

  _renderForm(p) {
    const t = this._t;
    const carrierOptions = Object.entries(CARRIERS)
      .map(([k, v]) => `<option value="${k}"${p.carrier === k ? ' selected' : ''}>${v}</option>`)
      .join('');
    const isNew = !p.tracking;
    return `
      <div class="card editing">
        <div style="font-weight:500;color:var(--primary-text-color);margin-bottom:4px">
          ${isNew ? t.new_parcel : t.edit_parcel}
        </div>
        <label>${t.name_label}</label>
        <input id="edit-name" type="text" value="${this._esc(p.friendly_name)}" placeholder="${t.name_placeholder}">
        <label>${t.tracking_label}</label>
        <input id="edit-tracking" type="text" value="${this._esc(p.tracking)}" placeholder="${t.tracking_placeholder}">
        <label>${t.carrier_label}</label>
        <select id="edit-carrier">${carrierOptions}</select>
        <div class="actions">
          <button class="btn-primary" data-action="save" data-slot="${p.slot}" ${this._saving ? 'disabled' : ''}>
            ${this._saving ? t.saving : t.save}
          </button>
          <button class="btn-secondary" data-action="cancel">${t.cancel}</button>
        </div>
      </div>
    `;
  }

  _renderAddButton(p) {
    const t = this._t;
    return `
      <div class="add-card" data-action="add" data-slot="${p.slot}">
        <div class="add-icon">+</div>
        <div class="add-label">${t.add_parcel}</div>
      </div>
    `;
  }

  _bindEvents() {
    const root = this.shadowRoot;
    const t = this._t;

    root.querySelector('#btn-refresh')?.addEventListener('click', () => this._refresh());

    root.querySelectorAll('[data-action]').forEach(el => {
      el.addEventListener('click', () => {
        const action = el.dataset.action;
        const slot = el.dataset.slot ? +el.dataset.slot : null;

        if (action === 'edit' || action === 'add') {
          this._editing = slot;
          this._render();
        } else if (action === 'cancel') {
          this._editing = null;
          this._render();
        } else if (action === 'delete') {
          if (confirm(t.confirm_delete)) {
            this._save(slot, '', 'auto', `Parcel ${slot}`);
          }
        } else if (action === 'save') {
          const tracking = root.querySelector('#edit-tracking')?.value || '';
          const carrier = root.querySelector('#edit-carrier')?.value || 'auto';
          const name = root.querySelector('#edit-name')?.value || '';
          this._save(slot, tracking, carrier, name);
        }
      });
    });
  }

  _formatTime(date) {
    const t = this._t;
    const diffMs = Date.now() - date.getTime();
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return t.just_now;
    if (diffMin < 60) return `${diffMin} ${t.min_ago}`;
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  _esc(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
}

customElements.define('parcel-tracker-panel', ParcelTrackerPanel);
