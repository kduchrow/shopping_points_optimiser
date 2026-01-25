/**
 * Popup Script für Shopping Points Optimiser Extension
 */

// DOM Elemente - Mit Null-Checks
const elements = {
  loading: document.getElementById("loading"),
  shopFound: document.getElementById("shop-found"),
  shopNotFound: document.getElementById("shop-not-found"),
  error: document.getElementById("error"),
  errorMessage: document.getElementById("error-message"),

  // Shop Found Elements
  shopName: document.getElementById("shop-name"),
  shopUrl: document.getElementById("shop-url"),
  bestRateContent: document.getElementById("best-rate-content"),
  ratesList: document.getElementById("rates-list"),
  btnOpenWeb: document.getElementById("btn-open-web"),

  // Shop Not Found Elements
  loginRequired: document.getElementById("login-required"),
  createProposal: document.getElementById("create-proposal"),
  proposalSuccess: document.getElementById("proposal-success"),
  btnLogin: document.getElementById("btn-login"),
  btnCheckLogin: document.getElementById("btn-check-login"),
  shopSelect: document.getElementById("shop-select"),
  urlInput: document.getElementById("url-input"),
  proposalForm: document.getElementById("proposal-form"),
  proposalBestRate: document.getElementById("proposal-best-rate"),
  proposalRatesList: document.getElementById("proposal-rates-list"),

  // Error Elements
  btnRetry: document.getElementById("btn-retry"),
};

/**
 * Extrahiert die Top-Level-Domain aus einer URL
 * z.B. https://www.amazon.de/gp/cart/view.html -> https://amazon.de
 */
function extractDomainUrl(url) {
  try {
    const urlObj = new URL(url);
    const parts = urlObj.hostname.split(".");
    // Nimm die letzten 2 Teile (domain.tld)
    const tld = parts.length >= 2 ? parts.slice(-2).join(".") : urlObj.hostname;
    // Gebe nur Protokoll + TLD zurück
    return `${urlObj.protocol}//${tld}`;
  } catch (error) {
    console.error("Error extracting domain URL:", error);
    return url;
  }
}

let currentTab = null;
let currentUrl = null;
let isLoggedIn = false;
let shopSearchDebounce = null;

/**
 * Zeigt einen View an und versteckt alle anderen
 */
function showView(viewName) {
  // Sicher verstecke alle Views
  if (elements.loading) elements.loading.classList.add("hidden");
  if (elements.shopFound) elements.shopFound.classList.add("hidden");
  if (elements.shopNotFound) elements.shopNotFound.classList.add("hidden");
  if (elements.error) elements.error.classList.add("hidden");

  // Zeige den gewünschten View
  switch (viewName) {
    case "loading":
      if (elements.loading) elements.loading.classList.remove("hidden");
      break;
    case "shop-found":
      if (elements.shopFound) elements.shopFound.classList.remove("hidden");
      break;
    case "shop-not-found":
      if (elements.shopNotFound) elements.shopNotFound.classList.remove("hidden");
      break;
    case "error":
      if (elements.error) elements.error.classList.remove("hidden");
      break;
  }
}

/**
 * Zeigt einen Fehler an
 */
function showError(message) {
  if (elements.errorMessage) elements.errorMessage.textContent = message;
  showView("error");
}

/**
 * Verarbeitet Fehlerhafte API-Antworten
 */
async function handleFetchError(response) {
  const contentType = response.headers.get("content-type");

  if (contentType?.includes("application/json")) {
    try {
      return await response.json();
    } catch (e) {
      console.error("Failed to parse JSON error response:", e);
      return { error: "Unerwartete Serverfehler" };
    }
  } else {
    // HTML error page
    const text = await response.text();
    console.error("Server returned HTML instead of JSON:", text.substring(0, 200));
    return { error: "Serverfehler - Bitte versuche es später erneut" };
  }
}

/**
 * Prüft ob User eingeloggt ist
 */
async function checkLoginStatus() {
  try {
    console.log("Checking login status at:", API_BASE_URL);
    const response = await fetch(`${API_BASE_URL}/api/user/status`, {
      credentials: "include",
    });

    if (!response.ok) {
      console.error(`Login status check failed with status: ${response.status}`);
      const errorData = await handleFetchError(response);
      throw new Error(errorData.error || "Login-Status konnte nicht abgerufen werden");
    }

    const data = await response.json();
    isLoggedIn = data.logged_in || false;
    console.log("Login status:", isLoggedIn);
    return isLoggedIn;
  } catch (error) {
    console.error("Error checking login status:", error);
    return false;
  }
}

/**
 * Sucht Shops basierend auf Suchbegriff (wie Index-Seite)
 */
async function searchShops(query) {
  try {
    if (!query || query.length < 2) {
      return [];
    }
    console.log("Searching shops with query:", query);
    const response = await fetch(`${API_BASE_URL}/shop_names?q=${encodeURIComponent(query)}`);

    if (!response.ok) {
      console.error(`Shop search failed with status: ${response.status}`);
      return [];
    }

    const shops = await response.json();
    console.log("Found shops:", shops.length);
    return shops;
  } catch (error) {
    console.error("Error searching shops:", error);
    return [];
  }
}

/**
 * Initialisiert Shop-Suche mit Debouncing
 */
function setupShopSearch() {
  if (!elements.shopSelect) return;

  // Erstelle Datalist für Autocomplete
  const datalistId = "shop-suggestions";
  let datalist = document.getElementById(datalistId);
  if (!datalist) {
    datalist = document.createElement("datalist");
    datalist.id = datalistId;
    elements.shopSelect.parentElement.appendChild(datalist);
  }

  // Konvertiere Select zu Input mit Autocomplete
  const searchInput = document.createElement("input");
  searchInput.type = "text";
  searchInput.id = "shop-search-input";
  searchInput.className = elements.shopSelect.className;
  searchInput.placeholder = "Shop suchen (mind. 2 Zeichen)...";
  searchInput.setAttribute("list", datalistId);
  searchInput.setAttribute("autocomplete", "off");
  searchInput.required = true;

  // Verstecke Original-Select, speichere aber die Referenz
  const hiddenSelect = elements.shopSelect;
  hiddenSelect.style.display = "none";
  hiddenSelect.removeAttribute("required"); // Entferne required von verstecktem Select
  hiddenSelect.parentElement.insertBefore(searchInput, hiddenSelect);

  // Event-Listener für Suche
  searchInput.addEventListener("input", async (e) => {
    const query = e.target.value.trim();

    // Prüfe ob ein Shop aus der Liste gewählt wurde
    const option = Array.from(datalist.options).find((opt) => opt.value === query);
    if (option && option.dataset.shopId) {
      hiddenSelect.value = option.dataset.shopId;
      console.log("Shop selected via input:", query, "ID:", option.dataset.shopId);
      return; // Keine neue Suche nötig
    }

    // Debounce für Suche
    if (shopSearchDebounce) {
      clearTimeout(shopSearchDebounce);
    }

    shopSearchDebounce = setTimeout(async () => {
      const shops = await searchShops(query);

      // Update Datalist
      datalist.innerHTML = "";
      shops.forEach((shop) => {
        const option = document.createElement("option");
        option.value = shop.name;
        option.dataset.shopId = shop.id;
        datalist.appendChild(option);
      });

      // Update Hidden Select
      hiddenSelect.innerHTML = '<option value="">-- Shop auswählen --</option>';
      shops.forEach((shop) => {
        const option = document.createElement("option");
        option.value = shop.id;
        option.textContent = shop.name;
        hiddenSelect.appendChild(option);
      });
    }, 300);
  });

  // Event-Listener für Auswahl (Fallback)
  searchInput.addEventListener("change", (e) => {
    const selectedName = e.target.value;
    // Finde die entsprechende Option im Datalist
    const option = Array.from(datalist.options).find((opt) => opt.value === selectedName);
    if (option && option.dataset.shopId) {
      hiddenSelect.value = option.dataset.shopId;
      console.log("Shop selected via change:", selectedName, "ID:", option.dataset.shopId);
    }
  });

  console.log("Shop search initialized");
}

/**
 * Lädt die Rates für einen Shop
 */
async function loadRates(shopId) {
  try {
    console.log("Loading rates for shop:", shopId);
    const response = await fetch(`${API_BASE_URL}/api/shops/${shopId}/rates`);

    if (!response.ok) {
      console.error(`Rates request failed with status: ${response.status}`);
      const errorData = await handleFetchError(response);
      throw new Error(errorData.error || "Rates konnten nicht geladen werden");
    }

    const data = await response.json();
    console.log("Loaded programs:", data.programs?.length || 0);
    return data.programs || [];
  } catch (error) {
    console.error("Error loading rates:", error);
    return [];
  }
}

/**
 * Rendert eine Rate-Card für ein Bonusprogramm
 */
function renderProgramCard(program) {
  const bestRate = program.rates.reduce((best, current) => {
    return current.effective_value > best.effective_value ? current : best;
  });

  const pointsPerEur = bestRate.points_per_eur || 0;
  const cashbackPct = bestRate.cashback_pct || 0;
  const effectiveValue = bestRate.effective_value || 0;

  let rateDisplay = "";
  const parts = [];

  if (pointsPerEur > 0) {
    parts.push(`${pointsPerEur} Punkte/€`);
  }
  if (cashbackPct > 0) {
    parts.push(`${cashbackPct}% Cashback`);
  }

  if (parts.length > 0) {
    rateDisplay = parts.join(" + ");
    rateDisplay += ` (≈ ${(effectiveValue * 100).toFixed(2)}€ Wert pro 100€)`;
  } else {
    rateDisplay = "Rate nicht verfügbar";
  }

  return `
    <div class="rate-card">
      <div class="rate-program">${program.program}</div>
      <div class="rate-value">${rateDisplay}</div>
      ${bestRate.incentive_text ? `<div class="rate-incentive">${bestRate.incentive_text}</div>` : ""}
    </div>
  `;
}

/**
 * Zeigt die Rates für einen Shop an (gruppiert nach Programm)
 */
function displayRates(programs, bestRateElement, ratesListElement) {
  if (!bestRateElement || !ratesListElement) {
    console.error("Missing rate display elements");
    return;
  }

  if (programs.length === 0) {
    bestRateElement.innerHTML = "<p>Keine Rates verfügbar</p>";
    ratesListElement.innerHTML = "<p>Keine Rates verfügbar</p>";
    return;
  }

  // Best program is already first (sorted by API)
  const bestProgram = programs[0];

  // Zeige bestes Programm
  bestRateElement.innerHTML = renderProgramCard(bestProgram);

  // Zeige alle Programme
  ratesListElement.innerHTML = programs.map((program) => renderProgramCard(program)).join("");
}

/**
 * Initialisiert das Popup
 */
async function initialize() {
  console.log("Initializing popup...");
  showView("loading");

  try {
    // Hole aktuelle Tab-Info
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tabs || !tabs[0]) {
      throw new Error("Keine aktive Tab gefunden");
    }

    currentTab = tabs[0];
    currentUrl = currentTab.url;
    console.log("Current URL:", currentUrl);

    // Hole erkannten Shop aus Storage
    const result = await chrome.storage.local.get([`shop_${currentTab.id}`]);
    const matchedShop = result[`shop_${currentTab.id}`];

    if (matchedShop) {
      console.log("Shop matched:", matchedShop.name);
      // Shop wurde erkannt
      if (elements.shopName) elements.shopName.textContent = matchedShop.name;
      if (elements.shopUrl) elements.shopUrl.textContent = matchedShop.url;

      // Lade Programme mit Rates
      const programs = await loadRates(matchedShop.id);
      displayRates(programs, elements.bestRateContent, elements.ratesList);

      showView("shop-found");
    } else {
      console.log("Shop not matched - showing proposal form");
      // Shop nicht erkannt
      // Extrahiere nur die Top-Level-Domain für das Proposal
      const domainUrl = extractDomainUrl(currentUrl);
      console.log("Domain URL for proposal:", domainUrl);
      if (elements.urlInput) elements.urlInput.value = domainUrl;

      // Prüfe Login-Status
      const loggedIn = await checkLoginStatus();

      if (loggedIn) {
        console.log("User is logged in - showing form");
        // Zeige Proposal-Formular mit Shop-Suche
        setupShopSearch();
        if (elements.loginRequired) elements.loginRequired.classList.add("hidden");
        if (elements.createProposal) elements.createProposal.classList.remove("hidden");
      } else {
        console.log("User is not logged in - showing login prompt");
        // Zeige Login-Aufforderung
        if (elements.loginRequired) elements.loginRequired.classList.remove("hidden");
        if (elements.createProposal) elements.createProposal.classList.add("hidden");
      }

      showView("shop-not-found");
    }
  } catch (error) {
    console.error("Initialization error:", error);
    showError("Fehler beim Laden der Daten. Bitte überprüfe deine Verbindung.");
  }
}

/**
 * Erstellt ein URL-Proposal
 */
async function createProposal(shopId, url) {
  try {
    console.log("Creating proposal for shop:", shopId);
    const response = await fetch(`${API_BASE_URL}/api/proposals/url`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify({
        shop_id: shopId,
        url: url,
      }),
    });

    if (!response.ok) {
      console.error(`Proposal request failed with status: ${response.status}`);
      const errorData = await handleFetchError(response);
      throw new Error(errorData.error || "Fehler beim Erstellen des Proposals");
    }

    const result = await response.json();
    console.log("Proposal created successfully");
    return result;
  } catch (error) {
    console.error("Error creating proposal:", error);
    throw error;
  }
}

// Event Listeners
if (elements.btnOpenWeb) {
  elements.btnOpenWeb.addEventListener("click", () => {
    chrome.tabs.create({ url: `${API_BASE_URL}/` });
  });
}

if (elements.btnLogin) {
  elements.btnLogin.addEventListener("click", () => {
    // Öffne Login-Seite in neuem Tab
    chrome.tabs.create({ url: `${API_BASE_URL}/login` }, (tab) => {
      // Warte auf Tab-Updates (wenn User sich einloggt)
      const tabId = tab.id;
      const listener = (updatedTabId, changeInfo, updatedTab) => {
        // Prüfe ob der User zurück zur Hauptseite navigiert hat (nach Login)
        if (
          updatedTabId === tabId &&
          changeInfo.status === "complete" &&
          updatedTab.url &&
          updatedTab.url.startsWith(API_BASE_URL) &&
          !updatedTab.url.includes("/login")
        ) {
          // User hat sich wahrscheinlich eingeloggt, prüfe Status neu
          setTimeout(() => {
            initialize();
          }, 1000);
          chrome.tabs.onUpdated.removeListener(listener);
        }
      };
      chrome.tabs.onUpdated.addListener(listener);

      // Cleanup nach 5 Minuten
      setTimeout(
        () => {
          chrome.tabs.onUpdated.removeListener(listener);
        },
        5 * 60 * 1000,
      );
    });
  });
}

if (elements.btnRetry) {
  elements.btnRetry.addEventListener("click", () => {
    initialize();
  });
}

if (elements.btnCheckLogin) {
  elements.btnCheckLogin.addEventListener("click", async () => {
    showView("loading");
    const loggedIn = await checkLoginStatus();
    if (loggedIn) {
      // User ist jetzt eingeloggt, neu initialisieren
      await initialize();
    } else {
      // Immer noch nicht eingeloggt
      showView("shop-not-found");
      alert("Du bist noch nicht eingeloggt. Bitte melde dich zuerst an.");
    }
  });
}

if (elements.proposalForm) {
  elements.proposalForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const shopId = elements.shopSelect?.value;
    if (!shopId) {
      alert("Bitte wähle einen Shop aus");
      return;
    }

    try {
      showView("loading");
      // Verwende die bereinigte Domain-URL für das Proposal
      const domainUrl = extractDomainUrl(currentUrl);
      await createProposal(shopId, domainUrl);

      // Lade Programme mit Rates für den vorgeschlagenen Shop
      const programs = await loadRates(shopId);
      displayRates(programs, elements.proposalBestRate, elements.proposalRatesList);

      // Zeige Success View
      if (elements.proposalSuccess) {
        elements.proposalSuccess.classList.remove("hidden");
      }
      if (elements.createProposal) {
        elements.createProposal.classList.add("hidden");
      }
      showView("shop-not-found");

      // Aktualisiere Cache im Background Script
      chrome.runtime.sendMessage({ action: "refreshCache" });
    } catch (error) {
      showError("Fehler beim Erstellen des Vorschlags. Bitte versuche es erneut.");
    }
  });
}

// Initialisiere beim Laden des Popups
document.addEventListener("DOMContentLoaded", initialize);
