"use strict";
const $ = id => document.getElementById(id);
let selected = null, identifiers = [], message = "", logs = [], busy = false, admissionAttempted = false;
function notice(text, kind = "") { $("notice").textContent = text; $("notice").className = kind; }
function cell(row, value) { const td = document.createElement("td"); td.textContent = value ?? ""; row.append(td); }
function addLogs(entries = []) {
  logs = logs.concat(entries).slice(-500);
  $("log-rows").replaceChildren();
  for (const item of logs) {
    const tr = document.createElement("tr");
    for (const key of ["timestamp", "method", "resource", "endpoint", "status", "result", "fhir_id", "detail"]) cell(tr, item[key]);
    $("log-rows").append(tr);
  }
}
async function api(path, options) {
  const response = await fetch(path, options);
  let data;
  try { data = await response.json(); } catch { throw new Error("Réponse applicative illisible. Vérifiez les logs du serveur."); }
  addLogs(data.traces);
  if (!response.ok || !data.ok) throw new Error(data.message || "L’opération a échoué.");
  return data;
}
async function action(fn) {
  if (busy) return;
  busy = true;
  document.querySelectorAll("button").forEach(b => b.disabled = true);
  try { await fn(); } catch (error) { notice(error.message, "error"); }
  finally {
    busy = false;
    document.querySelectorAll("button").forEach(b => b.disabled = false);
    $("copy").disabled = !message;
    $("admit-button").disabled = admissionAttempted;
  }
}
function resetResult() {
  message = ""; $("copy").disabled = true;
  $("summary").textContent = "Aucune admission enregistrée dans ce parcours.";
  $("encounter-json").textContent = "Aucune admission enregistrée.";
  $("hl7-message").textContent = "Aucun message généré.";
  $("mapping-state").textContent = "";
  $("mapping-rows").replaceChildren(); $("warnings").replaceChildren();
}
function clearSelection() {
  selected = null; identifiers = []; admissionAttempted = false;
  $("admit-fields").disabled = true; $("identity").textContent = "Aucun patient sélectionné.";
  $("identifier-select").replaceChildren(); $("patient-json").textContent = "Aucune ressource chargée.";
  resetResult();
}
function patientLabel(p) {
  const n = (p.name || [])[0] || {};
  return [n.family, ...(n.given || []), "· FHIR " + p.id, p.birthDate || "Naissance non renseignée"].filter(Boolean).join(" ");
}
function selectPatient(p) {
  selected = p; admissionAttempted = false; resetResult();
  $("admit-fields").disabled = false; $("admit-button").disabled = false;
  const phone = (p.telecom || []).find(x => x.system === "phone");
  $("identity").textContent = patientLabel(p) + " · Sexe : " + (p.gender || "absent") + " · Téléphone : " + (phone?.value || "non renseigné");
  $("patient-json").textContent = JSON.stringify(p, null, 2);
  identifiers = (p.identifier || []).filter(x => x.value);
  $("identifier-select").replaceChildren();
  const empty = document.createElement("option"); empty.value = ""; empty.textContent = identifiers.length ? "Sélectionner un identifiant métier" : "Aucun identifiant métier : PID-3 restera vide";
  $("identifier-select").append(empty);
  identifiers.forEach((x, i) => {
    const option = document.createElement("option"); option.value = String(i);
    option.textContent = x.value + (x.system ? " · " + x.system : " · système absent");
    $("identifier-select").append(option);
  });
  if (identifiers.length === 1) $("identifier-select").value = "0";
  notice("Patient sélectionné. Vérifiez son identité avant l’admission.");
}
function showPatients(patients) {
  $("candidates").replaceChildren();
  if (!patients.length) { notice("Aucun patient trouvé. Le CDC prévoit l’admission de patients existants uniquement."); return; }
  notice(patients.length + " patient(s) trouvé(s). Sélectionnez le patient à admettre.");
  for (const p of patients) {
    const button = document.createElement("button"); button.type = "button"; button.className = "candidate";
    button.textContent = patientLabel(p);
    button.addEventListener("click", () => { if (!busy) selectPatient(p); });
    $("candidates").append(button);
  }
  if (patients.length === 1) selectPatient(patients[0]);
}
$("search-form").addEventListener("submit", event => {
  event.preventDefault();
  action(async () => {
    clearSelection(); $("candidates").replaceChildren();
    const params = new URLSearchParams(new FormData(event.target));
    if (params.get("identifier")?.trim() && params.get("name")?.trim()) throw new Error("Rechercher par identifiant ou par nom, un seul critère à la fois.");
    notice("Recherche sur HAPI en cours…");
    const data = await api("/api/patients/search?" + params);
    showPatients(data.patients);
  });
});
$("read-form").addEventListener("submit", event => {
  event.preventDefault();
  action(async () => {
    clearSelection(); $("candidates").replaceChildren(); notice("Lecture sur HAPI en cours…");
    const id = new FormData(event.target).get("id").trim();
    selectPatient((await api("/api/patients/" + encodeURIComponent(id))).patient);
  });
});
function offsetTimestamp(value) {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) throw new Error("Date d’admission invalide.");
  const pad = x => String(x).padStart(2, "0");
  // Rejette une heure locale inexistante lors du passage à l’heure d’été.
  const local = d.getFullYear() + "-" + pad(d.getMonth()+1) + "-" + pad(d.getDate()) + "T" + pad(d.getHours()) + ":" + pad(d.getMinutes());
  if (value.slice(0,16) !== local) throw new Error("Cette heure locale n’existe pas dans le fuseau du navigateur.");
  const offset = -d.getTimezoneOffset();
  return local + ":" + pad(d.getSeconds()) + (offset < 0 ? "-" : "+") + pad(Math.floor(Math.abs(offset)/60)) + ":" + pad(Math.abs(offset)%60);
}
$("admit-form").addEventListener("submit", event => {
  event.preventDefault();
  action(async () => {
    if (!selected || admissionAttempted) return;
    const index = $("identifier-select").value;
    if (identifiers.length > 1 && index === "") throw new Error("Sélectionnez explicitement l’identifiant métier à utiliser.");
    const ident = index === "" ? {} : identifiers[Number(index)];
    const fields = Object.fromEntries(new FormData(event.target));
    const payload = {...fields, patient_id: selected.id, identifier_system: ident.system || "",
      identifier_value: ident.value || "", admission_time: offsetTimestamp(fields.admission_time)};
    resetResult(); notice("Enregistrement de l’admission sur HAPI…");
    admissionAttempted = true;
    let data;
    try {
      data = await api("/api/admissions", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
    } catch (error) {
      throw new Error(error.message + " Vérifiez les traces avant de sélectionner à nouveau le patient pour une nouvelle tentative.");
    }
    $("patient-json").textContent = JSON.stringify(data.patient, null, 2);
    $("encounter-json").textContent = JSON.stringify(data.encounter, null, 2);
    const s = data.summary;
    const title = document.createElement("h3"); title.textContent = "ADMISSION ENREGISTRÉE";
    const details = document.createElement("dl");
    const name = [s.name.family, ...(s.name.given || [])].filter(Boolean).join(" ");
    for (const [key, value] of Object.entries({"Patient":name || "Identité non renseignée", "Identifiant métier":s.identifier || "Non déterminé",
      "Identifiant FHIR Patient":s.patient_id, "Identifiant FHIR Encounter":s.encounter_id, "Admission":s.admission,
      "Service":s.location?.[0] || "Non renseigné", "Chambre":s.location?.[1] || "Non renseignée", "Lit":s.location?.[2] || "Non renseigné"})) {
      const dt=document.createElement("dt"), dd=document.createElement("dd"); dt.textContent=key; dd.textContent=value; details.append(dt,dd);
    }
    $("summary").replaceChildren(title,details);
    message=data.message; $("hl7-message").textContent=message.replace(/\r/g,"\n");
    $("mapping-state").textContent=data.complete ? "Transformation du noyau CDC complète." : "Transformation incomplète : champs non déterminés laissés vides. Message à examiner.";
    for (const warning of data.warnings) { const li=document.createElement("li"); li.textContent=warning; $("warnings").append(li); }
    for (const row of data.mapping) {
      const tr=document.createElement("tr");
      [row.concept, row.path + "\n" + (typeof row.source === "string" ? row.source : JSON.stringify(row.source)),
        row.rule + "\n" + row.kind, row.target, row.destination, row.issue].forEach(x=>cell(tr,x));
      $("mapping-rows").append(tr);
    }
    notice(data.complete ? "Admission enregistrée et message HL7 généré." : "Admission enregistrée ; transformation HL7 incomplète. Consultez les ambiguïtés.", data.complete ? "success" : "warning");
    $("result").scrollIntoView({behavior:"smooth"});
  });
});
$("copy").addEventListener("click", () => action(async()=>{await navigator.clipboard.writeText(message); notice("Message copié avec ses séparateurs de segments HL7.");}));
async function health() {
  $("server").textContent="Vérification…";
  try {
    const data=await api("/api/health");
    $("server").textContent="Connecté · FHIR " + data.server.fhirVersion;
    $("server").className="success";
  } catch(error) { $("server").textContent="Serveur indisponible"; $("server").className="error"; throw error; }
}
$("health").addEventListener("click",()=>action(health));
$("timezone").textContent="Fuseau utilisé : " + Intl.DateTimeFormat().resolvedOptions().timeZone + " (celui du navigateur ; décalage transmis à FHIR).";
action(health);

