/**
 * Popup Script für Shopping Points Optimiser Extension
 */

const API_BASE_URL = "http://localhost:5000";

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

let currentTab = null;
let currentUrl = null;
let isLoggedIn = false;

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
 * Lädt alle Shops für das Dropdown
 */
async function loadShopsForSelect() {
  try {
    console.log("Loading shops list...");
    const response = await fetch(`${API_BASE_URL}/api/shops`);

    if (!response.ok) {
      console.error(`Shops request failed with status: ${response.status}`);
      const errorData = await handleFetchError(response);
      throw new Error(errorData.error || "Shops konnten nicht geladen werden");
    }

    const data = await response.json();
    const shops = data.shops || [];
    console.log("Loaded shops:", shops.length);

    if (elements.shopSelect) {
      elements.shopSelect.innerHTML = '<option value="">-- Shop auswählen --</option>';
      shops.forEach((shop) => {
        const option = document.createElement("option");
        option.value = shop.id;
        option.textContent = shop.name;
        elements.shopSelect.appendChild(option);
      });
    }
  } catch (error) {
    console.error("Error loading shops:", error);
  }
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
    console.log("Loaded rates:", data.rates?.length || 0);
    return data.rates || [];
  } catch (error) {
    console.error("Error loading rates:", error);
    return [];
  }
}

/**
 * Rendert eine Rate-Card
 */
function renderRateCard(rate) {
  const value = rate.point_value_eur || 0.005;
  const pointsPerEur = rate.points_per_eur || 0;
  const cashbackPct = rate.cashback_pct || 0;

  let rateDisplay = "";
  if (pointsPerEur > 0) {
    const valuePerEur = pointsPerEur * value;
    rateDisplay = `${pointsPerEur} Punkte/€ (≈ ${valuePerEur.toFixed(2)}€ Wert)`;
  } else if (cashbackPct > 0) {
    rateDisplay = `${cashbackPct}% Cashback`;
  } else {
    rateDisplay = "Rate nicht verfügbar";
  }

  return `
    <div class="rate-card">
      <div class="rate-program">${rate.program || "Unbekannt"}</div>
      <div class="rate-value">${rateDisplay}</div>
      ${rate.incentive_text ? `<div class="rate-incentive">${rate.incentive_text}</div>` : ""}
    </div>
  `;
}

/**
 * Zeigt die Rates für einen Shop an
 */
function displayRates(rates, bestRateElement, ratesListElement) {
  if (!bestRateElement || !ratesListElement) {
    console.error("Missing rate display elements");
    return;
  }

  if (rates.length === 0) {
    bestRateElement.innerHTML = "<p>Keine Rates verfügbar</p>";
    ratesListElement.innerHTML = "<p>Keine Rates verfügbar</p>";
    return;
  }

  // Finde beste Rate
  const bestRate = rates.reduce((best, current) => {
    const bestValue = (best.points_per_eur || 0) * (best.point_value_eur || 0.005) + (best.cashback_pct || 0);
    const currentValue =
      (current.points_per_eur || 0) * (current.point_value_eur || 0.005) + (current.cashback_pct || 0);
    return currentValue > bestValue ? current : best;
  });

  // Zeige beste Rate
  bestRateElement.innerHTML = renderRateCard(bestRate);

  // Zeige alle Rates
  ratesListElement.innerHTML = rates.map((rate) => renderRateCard(rate)).join("");
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

      // Lade Rates
      const rates = await loadRates(matchedShop.id);
      displayRates(rates, elements.bestRateContent, elements.ratesList);

      showView("shop-found");
    } else {
      console.log("Shop not matched - showing proposal form");
      // Shop nicht erkannt
      if (elements.urlInput) elements.urlInput.value = currentUrl;

      // Prüfe Login-Status
      const loggedIn = await checkLoginStatus();

      if (loggedIn) {
        console.log("User is logged in - showing form");
        // Zeige Proposal-Formular
        await loadShopsForSelect();
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
      await createProposal(shopId, currentUrl);

      // Lade Rates für den vorgeschlagenen Shop
      const rates = await loadRates(shopId);
      displayRates(rates, elements.proposalBestRate, elements.proposalRatesList);

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
