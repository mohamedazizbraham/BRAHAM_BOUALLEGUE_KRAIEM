<script setup>
import { computed, ref } from 'vue'

const baseUrl = 'https://hapi.fhir.org/baseR4'
const searchType = ref('name')
const searchValue = ref('')
const patients = ref([])
const selectedPatient = ref(null)
const encounters = ref([])
const selectedEncounter = ref(null)
const organization = ref(null)
const practitioner = ref(null)
const location = ref(null)
const metadata = ref(null)
const activeTab = ref('business')
const loading = ref(false)
const errorMessage = ref('')
const logs = ref([])
const searchBundle = ref(null)
const hl7Version = ref('2.5.1')
const messageControlId = ref(generateControlId())
const lastError = ref('')

const resourceCount = computed(() => metadata.value?.rest?.[0]?.resource?.length || 0)
const patientName = computed(() => {
  const name = selectedPatient.value?.name?.[0]
  if (!name) return 'Patient non renseigné'
  const text = name.text || [...(name.given || []), name.family || ''].filter(Boolean).join(' ')
  return text || 'Patient non renseigné'
})
const birthDate = computed(() => selectedPatient.value?.birthDate || 'Information non disponible')
const gender = computed(() => selectedPatient.value?.gender || 'Information non disponible')
const businessIdentifier = computed(() => {
  const identifier = selectedPatient.value?.identifier?.[0]
  return identifier?.value || selectedPatient.value?.id || 'Information non disponible'
})
const identifierSystem = computed(() => selectedPatient.value?.identifier?.[0]?.system || 'Non renseigné')
const encounterClass = computed(() => {
  const c = selectedEncounter.value?.class
  return c ? [c.code, c.display].filter(Boolean).join(' — ') : 'Information non disponible'
})
const encounterType = computed(() => {
  const t = selectedEncounter.value?.type?.[0]
  return t ? [t.coding?.[0]?.code, t.coding?.[0]?.display || t.text].filter(Boolean).join(' — ') : 'Information non disponible'
})
const admissionDate = computed(() => formatDisplayDate(selectedEncounter.value?.period?.start))
const serviceName = computed(() => {
  const service = selectedEncounter.value?.serviceType
  return service ? [service.coding?.[0]?.code, service.coding?.[0]?.display || service.text].filter(Boolean).join(' — ') : 'Information non disponible'
})
const organizationName = computed(() => organization.value?.name || 'Information non disponible')
const practitionerName = computed(() => {
  const n = practitioner.value?.name?.[0]
  return n ? n.text || [...(n.given || []), n.family || ''].filter(Boolean).join(' ') : 'Information non disponible'
})
const locationName = computed(() => location.value?.name || 'Information non disponible')

const terminologyMapping = computed(() => {
  const source = selectedPatient.value?.gender
  if (!source) return null
  const map = {
    male: { target: 'M', meaning: 'Male / Masculin' },
    female: { target: 'F', meaning: 'Female / Féminin' },
    other: { target: 'O', meaning: 'Other / Autre' },
    unknown: { target: 'U', meaning: 'Unknown / Inconnu' },
  }
  const result = map[source]
  return result ? {
    source,
    sourceSystem: 'FHIR Patient.gender (administrative gender)',
    ...result,
    targetSystem: `HL7 v2 Table 0001 — version ${hl7Version.value}`,
  } : null
})

const hl7Message = computed(() => {
  if (!selectedPatient.value) return ''
  const p = selectedPatient.value
  const e = selectedEncounter.value
  const name = p.name?.[0] || {}
  const given = (name.given || []).join(' ')
  const family = name.family || ''
  const patientIdentifier = p.identifier?.[0]?.value || p.id || ''
  const idSystem = p.identifier?.[0]?.system || ''
  const sex = terminologyMapping.value?.target || ''
  const eventTime = formatHl7DateTime(e?.period?.start || new Date().toISOString())
  const sendingTime = formatHl7DateTime(new Date().toISOString())
  const visitNumber = e?.id || ''
  const patientClass = e?.class?.code || ''
  const msh = [
    'MSH', '^~\\&', 'ADMISSION-FHIR', 'HAPI-FHIR-R4', 'ADMISSION-HL7', 'PROTOTYPE',
    sendingTime, '', 'ADT^A01^ADT_A01', messageControlId.value, 'P', hl7Version.value,
  ]
  const evn = ['EVN', 'A01', eventTime]
  const cx = patientIdentifier ? `${patientIdentifier}^^^${idSystem || 'FHIR'}` : ''
  const pid = ['PID', '1', '', cx, '', `${family}^${given}`, '', p.birthDate || '', sex]
  const pv1 = ['PV1', '1', patientClass, '', '', '', '', '', '', '', '', '', '', '', '', '', '', visitNumber]
  return [msh.join('|'), evn.join('|'), pid.join('|'), pv1.join('|')].join('\r')
})

const mappingRows = computed(() => {
  const p = selectedPatient.value
  const e = selectedEncounter.value
  return [
    ['Patient.identifier[0].value', p?.identifier?.[0]?.value || p?.id || '—', 'PID-3', p?.identifier?.[0]?.value || p?.id || '—', 'Référence au premier identifiant patient disponible', 'Plusieurs identifiers possibles'],
    ['Patient.name.family / given', p?.name?.[0] ? `${p.name[0].family || ''} / ${(p.name[0].given || []).join(' ')}` : '—', 'PID-5', p?.name?.[0] ? `${p.name[0].family || ''}^${(p.name[0].given || []).join(' ')}` : '—', 'Assemblage dans le composant XPN', 'Structure différente si plusieurs noms'],
    ['Patient.birthDate', p?.birthDate || '—', 'PID-7', p?.birthDate || '—', 'Conservation du format date', 'Faible'],
    ['Patient.gender', p?.gender || '—', 'PID-8', terminologyMapping.value?.target || '—', 'Alignement terminologique', 'Dépend de la table cible'],
    ['Encounter.period.start', e?.period?.start || '—', 'EVN-2', e?.period?.start ? formatHl7DateTime(e.period.start) : '—', 'Conversion date/heure HL7', 'À confirmer selon version HL7 retenue'],
    ['Encounter.class.code', e?.class?.code || '—', 'PV1-2', e?.class?.code || '—', 'Reprise après vérification sémantique', 'À confirmer selon convention cible'],
    ['Encounter.id', e?.id || '—', 'PV1-19', e?.id || '—', 'Identifiant de visite du prototype', 'À confirmer par spécification/localisation HL7'],
  ]
})

function generateControlId() {
  return `CTRL-${Date.now().toString(36).toUpperCase()}`
}
function formatDisplayDate(value) {
  if (!value) return 'Information non disponible'
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? value : d.toLocaleString('fr-FR')
}
function formatHl7DateTime(value) {
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  const p = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}${p(d.getMonth()+1)}${p(d.getDate())}${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`
}
function addLog(method, endpoint, status, result) {
  logs.value.unshift({ time: new Date().toLocaleString('fr-FR'), method, endpoint, status, result })
  logs.value = logs.value.slice(0, 50)
}
function clearError() { errorMessage.value = ''; lastError.value = '' }

async function fhirGet(path) {
  clearError()
  const endpoint = `${baseUrl}/${path.replace(/^\//, '')}`
  loading.value = true
  try {
    const response = await fetch(endpoint, { headers: { Accept: 'application/fhir+json' } })
    let body = null
    try { body = await response.json() } catch { body = null }
    addLog('GET', `/${path.replace(/^\//, '')}`, response.status, response.ok ? 'Succès' : 'Erreur HTTP')
    if (!response.ok) {
      const diagnostics = body?.issue?.[0]?.diagnostics || body?.message || ''
      throw new Error(`HTTP ${response.status}${diagnostics ? ` — ${diagnostics}` : ''}`)
    }
    return body
  } catch (error) {
    lastError.value = error.message
    errorMessage.value = `Erreur de communication avec le serveur FHIR : ${error.message}`
    throw error
  } finally { loading.value = false }
}

async function checkServer() {
  try { metadata.value = await fhirGet('metadata') } catch {}
}

async function searchPatients() {
  clearError()
  if (!searchValue.value.trim()) {
    errorMessage.value = 'Saisissez une valeur de recherche.'
    return
  }
  selectedPatient.value = null
  selectedEncounter.value = null
  encounters.value = []
  organization.value = null
  practitioner.value = null
  location.value = null
  const params = new URLSearchParams({ _count: '20' })
  if (searchType.value === 'identifier') params.set('identifier', searchValue.value.trim())
  else if (searchType.value === 'family') params.set('family', searchValue.value.trim())
  else if (searchType.value === 'given') params.set('given', searchValue.value.trim())
  else params.set('name', searchValue.value.trim())

  try {
    const bundle = await fhirGet(`Patient?${params.toString()}`)
    searchBundle.value = bundle
    patients.value = (bundle?.entry || []).map(e => e.resource).filter(r => r?.resourceType === 'Patient')
    if (!patients.value.length) errorMessage.value = 'Aucun patient ne correspond à la recherche.'
  } catch {}
}

async function selectPatient(patient) {
  try {
    selectedPatient.value = await fhirGet(`Patient/${encodeURIComponent(patient.id)}`)
    await loadEncounters()
    activeTab.value = 'business'
  } catch {}
}

async function loadEncounters() {
  if (!selectedPatient.value?.id) return
  try {
    const bundle = await fhirGet(`Encounter?subject=Patient/${encodeURIComponent(selectedPatient.value.id)}&_count=20`)
    encounters.value = (bundle?.entry || []).map(e => e.resource).filter(r => r?.resourceType === 'Encounter')
    selectedEncounter.value = encounters.value[0] || null
    await loadLinkedResources()
  } catch {}
}

async function loadLinkedResources() {
  organization.value = null; practitioner.value = null; location.value = null
  const e = selectedEncounter.value
  const tasks = []
  const orgRef = e?.serviceProvider?.reference
  if (orgRef?.startsWith('Organization/')) tasks.push(fhirGet(orgRef).then(r => { organization.value = r }))
  const practRef = e?.participant?.find(p => p?.individual?.reference?.startsWith('Practitioner/'))?.individual?.reference
  if (practRef) tasks.push(fhirGet(practRef).then(r => { practitioner.value = r }))
  const locRef = e?.location?.find(l => l?.location?.reference?.startsWith('Location/'))?.location?.reference
  if (locRef) tasks.push(fhirGet(locRef).then(r => { location.value = r }))
  await Promise.allSettled(tasks)
}
async function selectEncounter(encounter) {
  selectedEncounter.value = encounter
  await loadLinkedResources()
}
function escapeHl7(value = '') {
  return String(value).replaceAll('\\', '\\\\').replaceAll('|', '\\F\\').replaceAll('^', '\\S\\').replaceAll('&', '\\T\\').replaceAll('~', '\\R\\')
}
const escapedMessage = computed(() => {
  const raw = hl7Message.value
  if (!raw) return ''
  return raw.split('\r').map(line => line.split('|').map((part, index) => index === 0 ? part : escapeHl7(part)).join('|')).join('\r')
})
</script>

<template>
  <div class="app-shell">
    <header class="hero">
      <div>
        <p class="eyebrow">Interopérabilité en santé · Réalisation</p>
        <h1>Admission patient</h1>
        <p class="subtitle">HAPI FHIR R4 réel → vue métier → ressources FHIR → HL7 v2 ADT^A01</p>
      </div>
      <div class="server-card">
        <span class="status-dot" :class="{ ok: metadata }"></span>
        <div><strong>HAPI FHIR R4</strong><small>{{ baseUrl }}</small></div>
      </div>
    </header>

    <main>
      <section class="panel connection-panel">
        <div class="section-head"><div><h2>1 · Connexion réelle</h2><p>Les données métier sont récupérées depuis le serveur, pas depuis le code.</p></div><button @click="checkServer" :disabled="loading">{{ metadata ? 'Actualiser' : 'Vérifier le serveur' }}</button></div>
        <div class="metadata-grid" v-if="metadata">
          <div><span>Version FHIR</span><strong>{{ metadata.fhirVersion }}</strong></div>
          <div><span>Ressources annoncées</span><strong>{{ resourceCount }}</strong></div>
          <div><span>Statut</span><strong>Connecté</strong></div>
        </div>
        <div v-else class="alert">Le serveur n'a pas encore été interrogé. Cliquez sur « Vérifier le serveur ».</div>
      </section>

      <section class="panel">
        <div class="section-head"><div><h2>2 · Recherche patient</h2><p>La recherche retourne un Bundle FHIR de type <code>searchset</code>.</p></div></div>
        <div class="search-row">
          <select v-model="searchType"><option value="name">Nom / texte</option><option value="identifier">Identifiant</option><option value="family">Nom de famille</option><option value="given">Prénom</option></select>
          <input v-model="searchValue" @keyup.enter="searchPatients" placeholder="Ex. SYN-000007" />
          <button @click="searchPatients" :disabled="loading">Rechercher</button>
        </div>
        <div class="alert error" v-if="errorMessage">{{ errorMessage }}</div>
        <div class="results" v-if="patients.length">
          <button class="patient-row" v-for="patient in patients" :key="patient.id" @click="selectPatient(patient)">
            <div><strong>{{ patient.name?.[0]?.text || [...(patient.name?.[0]?.given || []), patient.name?.[0]?.family || 'Patient'].filter(Boolean).join(' ') }}</strong><span>FHIR id : {{ patient.id }}</span><span>Identifiant : {{ patient.identifier?.[0]?.value || 'non renseigné' }}</span></div>
            <div class="row-meta">{{ patient.birthDate || 'Date non renseignée' }}</div>
          </button>
        </div>
        <div class="search-meta" v-if="searchBundle"><span>{{ patients.length }} résultat(s) affiché(s)</span><span>Type : {{ searchBundle.type || '—' }}</span><span>{{ searchBundle.link?.some(l => l.relation === 'next') ? 'Pagination disponible' : 'Fin des résultats' }}</span></div>
      </section>

      <section class="workspace" v-if="selectedPatient">
        <aside class="tabs-panel panel">
          <h3>Patient sélectionné</h3>
          <div class="mini-profile"><strong>{{ patientName }}</strong><span>{{ businessIdentifier }}</span><span class="tiny">FHIR id : {{ selectedPatient.id }}</span></div>
          <button :class="{ active: activeTab === 'business' }" @click="activeTab = 'business'">Vue métier</button>
          <button :class="{ active: activeTab === 'fhir' }" @click="activeTab = 'fhir'">Ressources FHIR</button>
          <button :class="{ active: activeTab === 'hl7' }" @click="activeTab = 'hl7'">Conversion HL7 v2</button>
          <button :class="{ active: activeTab === 'mapping' }" @click="activeTab = 'mapping'">Mapping</button>
          <button :class="{ active: activeTab === 'terminology' }" @click="activeTab = 'terminology'">Terminologie</button>
          <button :class="{ active: activeTab === 'trace' }" @click="activeTab = 'trace'">Traçabilité</button>
        </aside>

        <section class="panel content-panel">
          <div v-if="activeTab === 'business'">
            <div class="section-head"><div><h2>Vue métier</h2><p>Une synthèse lisible de l'identité et du séjour sélectionnés.</p></div></div>
            <div class="cards">
              <article class="info-card"><h3>Patient</h3><dl>
                <div><dt>Identifiant métier</dt><dd>{{ businessIdentifier }}</dd></div><div><dt>Système d'identification</dt><dd class="small-value">{{ identifierSystem }}</dd></div><div><dt>Nom</dt><dd>{{ patientName }}</dd></div><div><dt>Date de naissance</dt><dd>{{ birthDate }}</dd></div><div><dt>Sexe administratif</dt><dd>{{ gender }}</dd></div>
              </dl></article>
              <article class="info-card"><h3>Admission / séjour</h3><dl>
                <div><dt>Encounter</dt><dd>{{ selectedEncounter?.id || 'Information non disponible' }}</dd></div><div><dt>Statut</dt><dd>{{ selectedEncounter?.status || 'Information non disponible' }}</dd></div><div><dt>Classe</dt><dd>{{ encounterClass }}</dd></div><div><dt>Type</dt><dd>{{ encounterType }}</dd></div><div><dt>Date de début</dt><dd>{{ admissionDate }}</dd></div><div><dt>Établissement</dt><dd>{{ organizationName }}</dd></div><div><dt>Professionnel</dt><dd>{{ practitionerName }}</dd></div><div><dt>Localisation</dt><dd>{{ locationName }}</dd></div>
              </dl></article>
            </div>
            <div class="subpanel" v-if="encounters.length"><h3>Encounters liés au patient</h3><div class="encounters"><button v-for="encounter in encounters" :key="encounter.id" @click="selectEncounter(encounter)" :class="['encounter-chip', { selected: selectedEncounter?.id === encounter.id }]">{{ encounter.id }} · {{ encounter.status || 'statut inconnu' }}</button></div></div>
            <div class="alert" v-if="!encounters.length">Aucun Encounter n'a été retourné pour ce patient.</div>
          </div>

          <div v-else-if="activeTab === 'fhir'">
            <div class="section-head"><div><h2>Ressources FHIR réellement utilisées</h2><p>Les JSON affichés sont issus des réponses reçues du serveur.</p></div></div>
            <div class="resource-block"><h3>Patient</h3><pre>{{ JSON.stringify(selectedPatient, null, 2) }}</pre></div>
            <div class="resource-block" v-if="selectedEncounter"><h3>Encounter</h3><pre>{{ JSON.stringify(selectedEncounter, null, 2) }}</pre></div>
            <div class="resource-block" v-if="organization"><h3>Organization</h3><pre>{{ JSON.stringify(organization, null, 2) }}</pre></div>
            <div class="resource-block" v-if="practitioner"><h3>Practitioner</h3><pre>{{ JSON.stringify(practitioner, null, 2) }}</pre></div>
            <div class="resource-block" v-if="location"><h3>Location</h3><pre>{{ JSON.stringify(location, null, 2) }}</pre></div>
          </div>

          <div v-else-if="activeTab === 'hl7'">
            <div class="section-head"><div><h2>Conversion vers HL7 v2</h2><p>Représentation construite dynamiquement à partir du Patient et de l'Encounter sélectionnés.</p></div><button @click="messageControlId = generateControlId()">Nouveau contrôle</button></div>
            <div class="mapping-grid"><div><span>Source</span><strong>Patient + Encounter</strong></div><div><span>Message</span><strong>ADT^A01</strong></div><div><span>Identifiant contrôle</span><strong>{{ messageControlId }}</strong></div></div>
            <label class="field-label">Version HL7 v2 du prototype</label><input class="version-input" v-model="hl7Version" />
            <pre class="hl7">{{ escapedMessage }}</pre>
            <div class="subpanel"><h3>Segments produits</h3><div class="segment-grid"><span>MSH · en-tête</span><span>EVN · événement</span><span>PID · identité</span><span>PV1 · séjour</span></div></div>
            <div class="alert">La structure et les champs du message doivent encore être comparés à la spécification HL7 v2 exacte exigée par l'évaluation.</div>
          </div>

          <div v-else-if="activeTab === 'mapping'">
            <div class="section-head"><div><h2>Mapping FHIR → HL7 v2</h2><p>Traçabilité entre chaque valeur FHIR réelle et le champ cible.</p></div></div>
            <div class="table-wrap"><table><thead><tr><th>Source FHIR</th><th>Valeur réelle</th><th>Champ HL7</th><th>Valeur produite</th><th>Transformation</th><th>Risque</th></tr></thead><tbody><tr v-for="row in mappingRows" :key="row[0]"><td><code>{{ row[0] }}</code></td><td>{{ row[1] }}</td><td><strong>{{ row[2] }}</strong></td><td>{{ row[3] }}</td><td>{{ row[4] }}</td><td>{{ row[5] }}</td></tr></tbody></table></div>
          </div>

          <div v-else-if="activeTab === 'terminology'">
            <div class="section-head"><div><h2>Alignement de terminologie</h2><p>Cas concret basé sur la valeur <code>Patient.gender</code> réellement reçue.</p></div></div>
            <div v-if="terminologyMapping" class="term-card"><div><span>Code source</span><strong>{{ terminologyMapping.source }}</strong><small>{{ terminologyMapping.sourceSystem }}</small></div><div class="arrow">→</div><div><span>Code cible</span><strong>{{ terminologyMapping.target }}</strong><small>{{ terminologyMapping.targetSystem }}</small></div></div>
            <div v-if="terminologyMapping" class="subpanel"><h3>Signification</h3><p>{{ terminologyMapping.meaning }}</p><p class="muted">Règle utilisée : male → M, female → F, other → O, unknown → U.</p></div>
            <div v-else class="alert">Aucune valeur de terminologie exploitable n'est disponible.</div>
          </div>

          <div v-else>
            <div class="section-head"><div><h2>Traçabilité des échanges</h2><p>Journal minimal des requêtes effectuées par le prototype.</p></div></div>
            <div class="alert error" v-if="lastError">Dernière erreur : {{ lastError }}</div>
            <div class="table-wrap" v-if="logs.length"><table><thead><tr><th>Date</th><th>Méthode</th><th>Endpoint</th><th>HTTP</th><th>Résultat</th></tr></thead><tbody><tr v-for="(log, index) in logs" :key="index"><td>{{ log.time }}</td><td>{{ log.method }}</td><td><code>{{ log.endpoint }}</code></td><td>{{ log.status }}</td><td>{{ log.result }}</td></tr></tbody></table></div>
            <p v-else class="empty">Aucun échange journalisé.</p>
          </div>
        </section>
      </section>
    </main>
    <footer>Prototype d'évaluation · Données métier dynamiques issues de HAPI FHIR R4 · Aucun patient métier codé en dur.</footer>
  </div>
</template>
