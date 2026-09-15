const state = {
  config: null,
  patient: null,
  encounter: null,
  hl7: '',
  mappings: [],
  logs: [],
};

const $ = (id) => document.getElementById(id);

const els = {
  serverBadge: $('serverBadge'),
  checkServerBtn: $('checkServerBtn'),
  searchType: $('searchType'),
  searchInput: $('searchInput'),
  searchBtn: $('searchBtn'),
  searchError: $('searchError'),
  searchInfo: $('searchInfo'),
  results: $('results'),
  selectedSection: $('selectedSection'),
  selectedPatient: $('selectedPatient'),
  admitBtn: $('admitBtn'),
  admissionMessage: $('admissionMessage'),
  workspace: $('workspace'),
  businessView: $('businessView'),
  patientJson: $('patientJson'),
  encounterJson: $('encounterJson'),
  referenceCheck: $('referenceCheck'),
  hl7Output: $('hl7Output'),
  hl7Warnings: $('hl7Warnings'),
  mappingBody: $('mappingBody'),
  logsBody: $('logsBody'),
  copyHl7Btn: $('copyHl7Btn'),
  clearLogsBtn: $('clearLogsBtn'),
};

function showMessage(el, text, type = 'info') {
  el.textContent = text;
  el.className = `message ${type}`;
}
function hideMessage(el) { el.className = 'message hidden'; el.textContent = ''; }
function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}
function formatName(patient) {
  const name = patient?.name?.find((n) => n.use === 'official') || patient?.name?.[0];
  if (!name) return 'Nom indisponible';
  return [name.family, ...(name.given || [])].filter(Boolean).join(' ') || name.text || 'Nom indisponible';
}
function primaryIdentifier(patient) {
  const id = patient?.identifier?.find((x) => x.use === 'official') || patient?.identifier?.[0];
  return id?.value || null;
}
function displayOrUnavailable(value) { return value || 'Indisponible'; }
function isoToHl7Date(date) { return date ? String(date).replaceAll('-', '').slice(0, 8) : ''; }
function isoToHl7Timestamp(value) {
  if (!value) return '';
  const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?(?:\.(\d+))?(Z|[+-]\d{2}:?\d{2})?$/);
  if (!match) return '';
  const [, y, mo, d, h, mi, s = '00', , tz = ''] = match;
  let offset = tz;
  if (offset === 'Z') offset = '+0000';
  else offset = offset.replace(':', '');
  return `${y}${mo}${d}${h}${mi}${s}${offset}`;
}
function nowHl7() { return isoToHl7Timestamp(new Date().toISOString()); }
function hl7Escape(value) {
  return String(value ?? '')
    .replaceAll('\\', '\\E\\')
    .replaceAll('|', '\\F\\')
    .replaceAll('^', '\\S\\')
    .replaceAll('~', '\\R\\')
    .replaceAll('&', '\\T\\')
    .replaceAll('\r', ' ')
    .replaceAll('\n', ' ');
}
function operationOutcomeMessage(resource) {
  if (resource?.resourceType !== 'OperationOutcome') return null;
  const issues = resource.issue || [];
  return issues.map((i) => i.diagnostics || i.details?.text || `${i.severity || 'error'}: ${i.code || 'unknown'}`).join(' · ') || 'OperationOutcome retourné par le serveur FHIR.';
}
function logInteraction({ method, endpoint, status, result }) {
  state.logs.unshift({ time: new Date().toLocaleTimeString('fr-FR'), method, endpoint, status, result });
  renderLogs();
}
async function fhirRequest(path, options = {}) {
  const method = options.method || 'GET';
  const endpoint = path;
  try {
    const response = await fetch(`/api/fhir${path}`, {
      method,
      headers: {
        Accept: 'application/fhir+json',
        ...(options.body ? { 'Content-Type': 'application/fhir+json' } : {}),
      },
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
    const raw = await response.text();
    let resource = null;
    try { resource = raw ? JSON.parse(raw) : null; } catch { /* handled below */ }

    const oo = operationOutcomeMessage(resource);
    const result = response.ok ? (resource?.resourceType || 'Réponse reçue') : (oo || `Erreur HTTP ${response.status}`);
    logInteraction({ method, endpoint, status: response.status, result });

    if (!response.ok) {
      throw new Error(oo || `Erreur HTTP ${response.status}`);
    }
    if (!resource || typeof resource !== 'object') throw new Error('Réponse non JSON/FHIR reçue du serveur.');
    if (oo) throw new Error(oo);
    return { resource, status: response.status };
  } catch (error) {
    if (!state.logs[0] || state.logs[0].endpoint !== endpoint || state.logs[0].method !== method) {
      logInteraction({ method, endpoint, status: '—', result: error.message });
    }
    throw error;
  }
}

async function loadConfig() {
  const response = await fetch('/api/config');
  state.config = await response.json();
}
async function checkServer() {
  els.serverBadge.className = 'badge pending';
  els.serverBadge.textContent = 'Serveur : vérification…';
  try {
    const { resource } = await fhirRequest('/metadata');
    if (resource.resourceType !== 'CapabilityStatement') throw new Error(`resourceType inattendu: ${resource.resourceType}`);
    const version = resource.fhirVersion || 'R4 à confirmer';
    els.serverBadge.className = 'badge ok';
    els.serverBadge.textContent = `HAPI FHIR ${version} accessible`;
    return true;
  } catch (error) {
    els.serverBadge.className = 'badge error';
    els.serverBadge.textContent = 'Serveur inaccessible';
    showMessage(els.searchError, error.message, 'error');
    return false;
  }
}

async function searchPatients() {
  hideMessage(els.searchError); hideMessage(els.searchInfo);
  els.results.innerHTML = '';
  const type = els.searchType.value;
  const query = els.searchInput.value.trim();
  if (!query) return showMessage(els.searchError, 'Saisis un critère de recherche.', 'error');
  els.searchBtn.disabled = true;
  try {
    if (type === 'id') {
      const { resource } = await fhirRequest(`/Patient/${encodeURIComponent(query)}`);
      if (resource.resourceType !== 'Patient') throw new Error(`Patient attendu, ${resource.resourceType} reçu.`);
      renderResults([resource]);
      return;
    }
    const param = type === 'identifier' ? 'identifier' : 'name';
    const { resource } = await fhirRequest(`/Patient?${param}=${encodeURIComponent(query)}&_count=10`);
    if (resource.resourceType !== 'Bundle') throw new Error(`Bundle attendu, ${resource.resourceType} reçu.`);
    const patients = (resource.entry || []).map((e) => e.resource).filter((r) => r?.resourceType === 'Patient');
    if (!patients.length) showMessage(els.searchInfo, 'Aucun Patient trouvé pour ce critère.', 'info');
    renderResults(patients);
  } catch (error) {
    showMessage(els.searchError, error.message, 'error');
  } finally {
    els.searchBtn.disabled = false;
  }
}

function renderResults(patients) {
  els.results.innerHTML = '';
  if (!patients.length) return;
  patients.forEach((patient) => {
    const card = document.createElement('div');
    card.className = 'result-card';
    card.innerHTML = `
      <div>
        <strong>${escapeHtml(formatName(patient))}</strong>
        <small>FHIR id: ${escapeHtml(patient.id || '—')} · Identifiant: ${escapeHtml(primaryIdentifier(patient) || 'indisponible')} · Naissance: ${escapeHtml(patient.birthDate || '—')}</small>
      </div>
      <button class="secondary">Sélectionner</button>`;
    card.querySelector('button').addEventListener('click', () => selectPatient(patient));
    els.results.appendChild(card);
  });
}

function selectPatient(patient) {
  state.patient = patient;
  state.encounter = null;
  state.hl7 = '';
  state.mappings = [];
  els.selectedSection.classList.remove('hidden');
  els.workspace.classList.add('hidden');
  hideMessage(els.admissionMessage);
  els.selectedPatient.innerHTML = [
    ['Nom', formatName(patient)],
    ['FHIR id', patient.id],
    ['Identifiant métier', primaryIdentifier(patient)],
    ['Date de naissance', patient.birthDate],
    ['Sexe administratif', patient.gender],
  ].map(([label, value]) => `<div class="metric"><span>${label}</span><strong>${escapeHtml(displayOrUnavailable(value))}</strong></div>`).join('');
  els.selectedSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function admitPatient() {
  if (!state.patient?.id) return showMessage(els.admissionMessage, 'Patient invalide : id FHIR absent.', 'error');
  els.admitBtn.disabled = true;
  hideMessage(els.admissionMessage);
  const admissionTime = new Date().toISOString();
  const encounter = {
    resourceType: 'Encounter',
    status: 'in-progress',
    class: {
      system: 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
      code: 'IMP',
      display: 'inpatient encounter',
    },
    subject: { reference: `Patient/${state.patient.id}` },
    period: { start: admissionTime },
  };

  try {
    const { resource } = await fhirRequest('/Encounter', { method: 'POST', body: encounter });
    if (resource.resourceType !== 'Encounter') throw new Error(`Encounter attendu, ${resource.resourceType} reçu.`);
    if (resource.subject?.reference !== `Patient/${state.patient.id}`) {
      throw new Error(`Référence Patient incohérente dans Encounter.subject.reference: ${resource.subject?.reference || 'absente'}`);
    }
    state.encounter = resource;
    showMessage(els.admissionMessage, `Admission créée avec succès — Encounter/${resource.id}`, 'success');
    buildDemonstration();
    els.workspace.classList.remove('hidden');
    els.workspace.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) {
    showMessage(els.admissionMessage, `Admission non créée : ${error.message}`, 'error');
  } finally {
    els.admitBtn.disabled = false;
  }
}

function genderMapping(gender) {
  const sourceSystem = 'http://hl7.org/fhir/administrative-gender';
  const targetSystem = 'http://terminology.hl7.org/CodeSystem/v2-0001';
  const exact = { male: 'M', female: 'F', unknown: 'U' };
  if (exact[gender]) return { value: exact[gender], type: 'Équivalence terminologique', status: 'OK', sourceSystem, targetSystem, note: '' };
  if (gender === 'other') {
    return { value: '', type: 'Mapping sémantique', status: 'AMBIGU', sourceSystem, targetSystem, note: 'FHIR R4 ConceptMap propose plusieurs cibles plus étroites (A ou O) : aucune conversion automatique.' };
  }
  return { value: '', type: 'Correspondance non déterminée', status: 'ABSENT', sourceSystem, targetSystem, note: 'Source absente ou non reconnue.' };
}

function classMapping(encounterClassCode) {
  if (encounterClassCode === 'IMP') {
    return { value: 'I', type: 'Mapping sémantique', status: 'OK', sourceSystem: 'http://terminology.hl7.org/CodeSystem/v3-ActCode', targetSystem: 'HL7 v2 Table 0004 Patient Class', note: 'IMP (inpatient encounter) → I (Inpatient)' };
  }
  return { value: '', type: 'Correspondance non déterminée', status: 'ABSENT', sourceSystem: 'http://terminology.hl7.org/CodeSystem/v3-ActCode', targetSystem: 'HL7 v2 Table 0004 Patient Class', note: 'Classe non gérée par le MVP.' };
}

function buildHl7(patient, encounter) {
  const warnings = [];
  const mappings = [];
  const name = patient.name?.find((n) => n.use === 'official') || patient.name?.[0];
  const identifier = patient.identifier?.find((x) => x.use === 'official') || patient.identifier?.[0];
  const gender = genderMapping(patient.gender);
  const pClass = classMapping(encounter.class?.code);
  const admitTs = isoToHl7Timestamp(encounter.period?.start);

  if (!identifier?.value) warnings.push('PID-3 : Patient.identifier absent — identifiant métier non inventé.');
  if (!name?.family && !name?.given?.length && !name?.text) warnings.push('PID-5 : Patient.name absent — nom non inventé.');
  if (patient.gender === 'other') warnings.push('PID-8 : FHIR gender=other est ambigu vers HL7 v2 (A ou O selon le ConceptMap R4) — champ laissé vide.');
  if (!admitTs) warnings.push('PV1-44 : Encounter.period.start absent ou non convertible.');

  const msh = `MSH|^~\\&|FHIR-ADMISSION-APP|HAPI-FHIR|TARGET-HIS|DEMO|${nowHl7()}||ADT^A01|${crypto.randomUUID()}|T|2.5.1`;
  const evnFields = Array(3).fill(''); evnFields[0] = 'EVN'; evnFields[2] = nowHl7();
  const pidFields = Array(9).fill('');
  pidFields[0] = 'PID';
  pidFields[3] = hl7Escape(identifier?.value || '');
  const family = hl7Escape(name?.family || name?.text || '');
  const given = hl7Escape(name?.given?.[0] || '');
  pidFields[5] = (family || given) ? [family, given].join('^') : '';
  pidFields[7] = isoToHl7Date(patient.birthDate);
  pidFields[8] = gender.value;

  const pv1Fields = Array(45).fill('');
  pv1Fields[0] = 'PV1';
  pv1Fields[2] = pClass.value;
  const encounterIdentifier = encounter.identifier?.find((x) => x.use === 'official') || encounter.identifier?.[0];
  pv1Fields[19] = hl7Escape(encounterIdentifier?.value || encounter.id || '');
  pv1Fields[44] = admitTs;

  mappings.push(
    { source: `Patient.gender = ${patient.gender ?? 'absent'}`, sourceSystem: gender.sourceSystem, rule: `${patient.gender ?? '—'} → ${gender.value || '?'}`, target: `PID-8 = ${gender.value || 'vide'}`, type: gender.type, status: gender.status, note: gender.note },
    { source: `Encounter.class.code = ${encounter.class?.code ?? 'absent'}`, sourceSystem: pClass.sourceSystem, rule: `${encounter.class?.code ?? '—'} → ${pClass.value || '?'}`, target: `PV1-2 = ${pClass.value || 'vide'}`, type: pClass.type, status: pClass.status, note: pClass.note },
    { source: `Patient.birthDate = ${patient.birthDate ?? 'absent'}`, sourceSystem: 'FHIR date', rule: `${patient.birthDate || '—'} → ${isoToHl7Date(patient.birthDate) || '?'}`, target: `PID-7 = ${isoToHl7Date(patient.birthDate) || 'vide'}`, type: 'Transformation syntaxique', status: patient.birthDate ? 'OK' : 'ABSENT', note: 'Changement de format sans changement de sens.' },
    { source: `Encounter.period.start = ${encounter.period?.start ?? 'absent'}`, sourceSystem: 'FHIR dateTime', rule: `ISO 8601 → HL7 TS`, target: `PV1-44 = ${admitTs || 'vide'}`, type: 'Transformation syntaxique', status: admitTs ? 'OK' : 'ABSENT', note: 'Préserve date/heure et offset lorsqu’ils sont présents.' },
  );

  return { text: [msh, evnFields.join('|'), pidFields.join('|'), pv1Fields.join('|')].join('\r'), warnings, mappings };
}

function buildDemonstration() {
  const { patient, encounter } = state;
  const conversion = buildHl7(patient, encounter);
  state.hl7 = conversion.text;
  state.mappings = conversion.mappings;

  els.businessView.innerHTML = [
    ['Patient', formatName(patient)],
    ['Identifiant métier', primaryIdentifier(patient)],
    ['Date de naissance', patient.birthDate],
    ['Sexe administratif', patient.gender],
    ['Statut admission', encounter.status],
    ['Classe FHIR', encounter.class?.code],
    ['Date / heure admission', encounter.period?.start],
    ['Encounter id', encounter.id],
  ].map(([label, value]) => `<div class="metric"><span>${label}</span><strong>${escapeHtml(displayOrUnavailable(value))}</strong></div>`).join('');

  els.patientJson.textContent = JSON.stringify(patient, null, 2);
  els.encounterJson.textContent = JSON.stringify(encounter, null, 2);
  const expectedRef = `Patient/${patient.id}`;
  const actualRef = encounter.subject?.reference;
  els.referenceCheck.textContent = `Référence vérifiée : Encounter.subject.reference = ${actualRef || 'absente'} ${actualRef === expectedRef ? '✓' : '✗'} (attendu : ${expectedRef})`;

  els.hl7Output.textContent = state.hl7.replaceAll('\r', '\n');
  els.hl7Warnings.innerHTML = conversion.warnings.length
    ? conversion.warnings.map((w) => `<div class="message warning">${escapeHtml(w)}</div>`).join('')
    : '<div class="message success">Aucun avertissement de transformation détecté pour les champs du MVP.</div>';
  renderMappings();
}

function renderMappings() {
  els.mappingBody.innerHTML = state.mappings.map((m) => `
    <tr>
      <td>${escapeHtml(m.source)}</td>
      <td>${escapeHtml(m.sourceSystem)}</td>
      <td>${escapeHtml(m.rule)}${m.note ? `<br><small>${escapeHtml(m.note)}</small>` : ''}</td>
      <td>${escapeHtml(m.target)}</td>
      <td>${escapeHtml(m.type)}</td>
      <td><span class="status-pill ${m.status === 'OK' ? 'ok' : 'warn'}">${escapeHtml(m.status)}</span></td>
    </tr>`).join('');
}

function renderLogs() {
  els.logsBody.innerHTML = state.logs.map((l) => `
    <tr><td>${escapeHtml(l.time)}</td><td>${escapeHtml(l.method)}</td><td>${escapeHtml(l.endpoint)}</td><td>${escapeHtml(l.status)}</td><td>${escapeHtml(l.result)}</td></tr>`).join('');
}

function initTabs() {
  document.querySelectorAll('.tab').forEach((button) => {
    button.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach((b) => b.classList.toggle('active', b === button));
      document.querySelectorAll('.tab-content').forEach((content) => content.classList.remove('active'));
      $(`tab-${button.dataset.tab}`).classList.add('active');
    });
  });
}

els.searchBtn.addEventListener('click', searchPatients);
els.searchInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') searchPatients(); });
els.checkServerBtn.addEventListener('click', checkServer);
els.admitBtn.addEventListener('click', admitPatient);
els.copyHl7Btn.addEventListener('click', async () => {
  if (!state.hl7) return;
  await navigator.clipboard.writeText(state.hl7);
  els.copyHl7Btn.textContent = 'Copié ✓';
  setTimeout(() => { els.copyHl7Btn.textContent = 'Copier'; }, 1200);
});
els.clearLogsBtn.addEventListener('click', () => { state.logs = []; renderLogs(); });
initTabs();

await loadConfig();
await checkServer();
