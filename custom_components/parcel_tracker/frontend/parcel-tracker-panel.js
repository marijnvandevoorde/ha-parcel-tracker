const CARRIERS = {
  auto: 'Auto-detect',
  bpost: 'bPost',
  dhl: 'DHL',
  tnt: 'TNT / FedEx',
  ups: 'UPS',
  postnl: 'PostNL',
};

const STATUS = {
  delivered:        { label: 'Bezorgd',            color: '#4CAF50' },
  in_transit:       { label: 'Onderweg',            color: '#2196F3' },
  out_for_delivery: { label: 'Wordt vandaag bezorgd', color: '#FF9800' },
  pending:          { label: 'Aangemeld',           color: '#9E9E9E' },
  exception:        { label: 'Probleem',            color: '#F44336' },
  unknown:          { label: 'Onbekend',            color: '#9E9E9E' },
  empty:            { label: '',                    color: 'transparent' },
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
    this._editing = null;
    this._loading = true;
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

  async _loadData() {
    this._loading = true;
    this._render();
    try {
      const result = await this._hass.callWS({ type: 'parcel_tracker/list' });
      if (result && result.length > 0) {
        this._entryId = result[0].entry_id;
        this._parcels = result[0].parcels;
      }
    } catch (e) {
      this._showToast('error', 'Kon pakketdata niet laden. Controleer of de integratie actief is.');
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
      this._showToast('success', tracking.trim() ? 'Pakket opgeslagen!' : 'Pakket verwijderd.');
      await this._loadData();
    } catch (e) {
      this._showToast('error', 'Opslaan mislukt. Probeer opnieuw.');
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
    if (this._loading) {
      return `<h1>📦 Parcel Tracker</h1><div class="loading">Laden…</div>`;
    }
    const active = this._parcels.filter(p => p.tracking);
    const nextEmpty = this._parcels.find(p => !p.tracking);

    return `
      <div class="toolbar">
        <h1>📦 Parcel Tracker</h1>
        <button class="btn-secondary btn-sm" id="btn-refresh">↻ Ververs</button>
      </div>
      ${this._toast ? `<div class="toast ${this._toast.type}">${this._esc(this._toast.text)}</div>` : ''}
      ${active.length === 0 && this._editing === null ? this._renderEmptyState() : ''}
      ${active.length > 0 ? '<div class="section-label">Actieve pakketten</div>' : ''}
      ${active.map(p => this._editing === p.slot ? this._renderForm(p) : this._renderParcel(p)).join('')}
      ${nextEmpty
        ? (this._editing === nextEmpty.slot
            ? this._renderForm(nextEmpty)
            : this._renderAddButton(nextEmpty))
        : '<div style="font-size:0.8rem;color:var(--secondary-text-color);text-align:center">Maximum van 10 pakketten bereikt.</div>'
      }
    `;
  }

  _renderEmptyState() {
    return `
      <div class="empty-state">
        <div class="big">📦</div>
        <div style="margin-top:8px">Nog geen pakketten toegevoegd.</div>
        <div style="font-size:0.8rem;margin-top:4px">Klik hieronder om je eerste pakket in te voeren.</div>
      </div>
    `;
  }

  _renderParcel(p) {
    const st = STATUS[p.status] || STATUS.unknown;
    const carrierLabel = CARRIERS[p.carrier] || p.carrier;
    return `
      <div class="card" data-slot="${p.slot}">
        <div class="slot-header">
          <span class="slot-name">${this._esc(p.friendly_name)}</span>
          ${st.label ? `<span class="badge" style="background:${st.color}">${st.label}</span>` : ''}
        </div>
        <div class="tracking-num">${this._esc(p.tracking)}</div>
        <div class="carrier-label">
          ${this._esc(carrierLabel)}
          ${p.tracking_url ? ` &middot; <a href="${this._esc(p.tracking_url)}" target="_blank">Volg pakket →</a>` : ''}
        </div>
        ${p.status_detail ? `<div class="detail">${this._esc(p.status_detail)}</div>` : ''}
        <div class="actions">
          <button class="btn-secondary btn-sm" data-action="edit" data-slot="${p.slot}">Bewerken</button>
          <button class="btn-danger btn-sm" data-action="delete" data-slot="${p.slot}">Verwijderen</button>
        </div>
      </div>
    `;
  }

  _renderForm(p) {
    const carrierOptions = Object.entries(CARRIERS)
      .map(([k, v]) => `<option value="${k}"${p.carrier === k ? ' selected' : ''}>${v}</option>`)
      .join('');
    const isNew = !p.tracking;
    return `
      <div class="card editing">
        <div style="font-weight:500;color:var(--primary-text-color);margin-bottom:4px">
          ${isNew ? 'Nieuw pakket toevoegen' : 'Pakket bewerken'}
        </div>
        <label>Naam (optioneel)</label>
        <input id="edit-name" type="text" value="${this._esc(p.friendly_name)}" placeholder="bijv. Bestelling bol.com">
        <label>Trackingnummer</label>
        <input id="edit-tracking" type="text" value="${this._esc(p.tracking)}" placeholder="bijv. JD014600004860246190">
        <label>Bezorgdienst</label>
        <select id="edit-carrier">${carrierOptions}</select>
        <div class="actions">
          <button class="btn-primary" data-action="save" data-slot="${p.slot}" ${this._saving ? 'disabled' : ''}>
            ${this._saving ? 'Opslaan…' : 'Opslaan'}
          </button>
          <button class="btn-secondary" data-action="cancel">Annuleren</button>
        </div>
      </div>
    `;
  }

  _renderAddButton(p) {
    return `
      <div class="add-card" data-action="add" data-slot="${p.slot}">
        <div class="add-icon">+</div>
        <div class="add-label">Pakket toevoegen</div>
      </div>
    `;
  }

  _bindEvents() {
    const root = this.shadowRoot;

    root.querySelector('#btn-refresh')?.addEventListener('click', () => this._loadData());

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
          if (confirm('Pakket verwijderen?')) {
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

  _esc(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
}

customElements.define('parcel-tracker-panel', ParcelTrackerPanel);
