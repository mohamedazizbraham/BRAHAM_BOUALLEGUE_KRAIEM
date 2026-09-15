"""Vérification navigateur réelle ; crée un Encounter pour le Patient fictif fourni."""
import argparse
import json
from uuid import uuid4
from playwright.sync_api import sync_playwright, expect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patient-id", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    errors, external = [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width":1440,"height":1000}, timezone_id="Europe/Paris")
        page = context.new_page()
        page.on("pageerror", lambda error:errors.append(str(error)))
        page.on("request", lambda request:external.append(request.url) if "hapi.fhir.org" in request.url else None)
        page.goto(args.base_url)
        expect(page.locator("#server")).to_contain_text("Connecté", timeout=60000)
        expect(page.locator("nav a")).to_have_count(6)
        page.screenshot(path="docs/interface-desktop.png", full_page=True)
        page.set_viewport_size({"width":390,"height":844})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path="docs/interface-mobile.png", full_page=True)
        page.set_viewport_size({"width":1440,"height":1000})
        page.locator('#search-form input[name="identifier"]').fill("ABSENT-" + uuid4().hex)
        page.locator("#search-form button").click()
        expect(page.locator("#notice")).to_contain_text("Aucun patient trouvé", timeout=60000)
        expect(page.locator("#admit-button")).to_be_disabled()
        page.locator('#read-form input[name="id"]').fill(args.patient_id)
        page.locator("#read-form button").click()
        expect(page.locator("#identity")).to_contain_text("FHIR " + args.patient_id, timeout=60000)
        patient = json.loads(page.locator("#patient-json").inner_text())
        assert any("test" in str(n).lower() or "demo" in str(n).lower() for n in patient.get("name", []))
        if page.locator("#identifier-select").input_value() == "":
            page.locator("#identifier-select").select_option("0")
        page.locator('#admit-form input[name="service"]').fill("Service test navigateur")
        page.locator('#admit-form input[name="room"]').fill("UI")
        page.locator('#admit-form input[name="bed"]').fill("TEST")
        page.locator('#admit-form input[name="admission_time"]').fill("2026-09-15T14:00")
        page.locator("#admit-button").click()
        expect(page.locator("#summary")).to_contain_text("ADMISSION ENREGISTRÉE", timeout=120000)
        expect(page.locator("#mapping-state")).to_contain_text("complète")
        expect(page.locator("#hl7-message")).to_contain_text("ADT^A01^ADT_A01")
        encounter = json.loads(page.locator("#encounter-json").inner_text())
        assert encounter["subject"]["reference"] == "Patient/" + args.patient_id
        assert encounter["period"]["start"].endswith("+02:00")
        assert page.locator("#mapping-rows tr").count() >= 14
        assert page.locator("#log-rows").inner_text().find("POST") >= 0
        assert page.locator("#admit-button").is_disabled()
        assert not external, external
        assert not errors, errors
        print(json.dumps({"ui":"passed", "patient_id":args.patient_id, "encounter_id":encounter["id"],
                          "views":6,"responsive":True,"browser_hapi_calls":len(external),
                          "javascript_errors":errors}), flush=True)
        context.close()
        browser.close()


if __name__ == "__main__":
    main()



