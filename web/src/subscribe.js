// @ts-check
/**
 * The opt-in alerts form. POSTs to the alerts API (infra/alerts) which stores a
 * pending subscriber and emails a confirm link (double opt-in). No account, no
 * client secret: abuse is bounded server-side. If the endpoint is not
 * configured, the form degrades to an explanation.
 */

const SUBSCRIBE_URL = /** @type {any} */ (window).SCORECARD_SUBSCRIBE_URL || null;
const DATA_BASES = [
  /** @type {any} */ (window).SCORECARD_DATA_BASE,
  "data/artifacts",
  "../data/artifacts",
].filter(Boolean);

const form = /** @type {HTMLFormElement} */ (document.getElementById("subscribe-form"));
const status = /** @type {HTMLElement} */ (document.getElementById("form-status"));
const agencySelect = /** @type {HTMLSelectElement} */ (document.getElementById("agency"));

/** Fetch index.json from the first base that answers, to fill the agency list. */
async function fetchIndex() {
  for (const base of DATA_BASES) {
    try {
      const res = await fetch(`${base}/index.json`);
      if (res.ok) return res.json();
    } catch {
      /* try the next base */
    }
  }
  return null;
}

async function populateAgencies() {
  const index = await fetchIndex();
  if (!index || !index.agencies) return;
  const entries = Object.entries(index.agencies)
    .map(([id, a]) => ({ id, name: /** @type {any} */ (a).name }))
    .sort((x, y) => x.name.localeCompare(y.name));
  for (const { id, name } of entries) {
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = name;
    agencySelect.appendChild(opt);
  }
}

function setStatus(message, kind) {
  status.textContent = message;
  status.className = `form-status ${kind || ""}`.trim();
}

if (!SUBSCRIBE_URL) {
  setStatus(
    "Alerts are not enabled on this deployment yet. Check back soon.",
    "form-error"
  );
  if (form) form.querySelector("button")?.setAttribute("disabled", "true");
} else {
  populateAgencies();
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const email = String(data.get("email") || "").trim();
    const agency = String(data.get("agency") || "");
    const kinds = data.getAll("kinds").map(String);
    if (!email) return setStatus("Enter your email.", "form-error");
    if (!kinds.length) return setStatus("Choose at least one kind of alert.", "form-error");

    const payload = agency ? { email, agencies: [agency], kinds } : { email, all: true, kinds };
    setStatus("Sending…", "");
    form.querySelector("button")?.setAttribute("disabled", "true");
    try {
      const res = await fetch(`${SUBSCRIBE_URL.replace(/\/$/, "")}/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await res.json().catch(() => ({}));
      if (res.ok) {
        setStatus(
          body.message || "Check your email to confirm your subscription.",
          "form-ok"
        );
        form.reset();
      } else if (res.status === 429) {
        setStatus(body.error || "Too many requests. Try again later.", "form-error");
      } else {
        setStatus(body.error || "Something went wrong. Please try again.", "form-error");
      }
    } catch {
      setStatus("Could not reach the server. Please try again.", "form-error");
    } finally {
      form.querySelector("button")?.removeAttribute("disabled");
    }
  });
}
