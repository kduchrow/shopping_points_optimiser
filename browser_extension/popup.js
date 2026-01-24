/**
 * Popup Script für Shopping Points Optimiser Extension
 */

const API_BASE_URL = "http://localhost:5000";

// DOM Elemente
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
  elements.loading.classList.add("hidden");
  elements.shopFound.classList.add("hidden");
  elements.shopNotFound.classList.add("hidden");
  elements.error.classList.add("hidden");

  switch (viewName) {
    case "loading":
      elements.loading.classList.remove("hidden");
      break;
    case "shop-found":
      elements.shopFound.classList.remove("hidden");
      break;
    case "shop-not-found":
      elements.shopNotFound.classList.remove("hidden");
      break;
    case "error":
      elements.error.classList.remove("hidden");
      break;
  }
}

/**
 * Zeigt einen Fehler an
 */
function showError(message) {
  elements.errorMessage.textContent = message;
  showView("error");
}

/**
 * Prüft ob User eingeloggt ist
 */
async function checkLoginStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/user/status`, {
      credentials: "include",
    });
    const data = await response.json();
    isLoggedIn = data.logged_in || false;
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
    const response = await fetch(`${API_BASE_URL}/api/shops`);
    const data = await response.json();
    const shops = data.shops || [];

    elements.shopSelect.innerHTML = '<option value="">-- Shop auswählen --</option>';
    shops.forEach((shop) => {
      const option = document.createElement("option");
      option.value = shop.id;
      option.textContent = shop.name;
      elements.shopSelect.appendChild(option);
    });
  } catch (error) {
    console.error("Error loading shops:", error);
  }
}

/**
 * Lädt die Rates für einen Shop
 */
async function loadRates(shopId) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/shops/${shopId}/rates`);
    const data = await response.json();
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
  showView("loading");

  try {
    // Hole aktuelle Tab-Info
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    currentTab = tabs[0];
    currentUrl = currentTab.url;

    // Hole erkannten Shop aus Storage
    const result = await chrome.storage.local.get([`shop_${currentTab.id}`]);
    const matchedShop = result[`shop_${currentTab.id}`];

    if (matchedShop) {
      // Shop wurde erkannt
      elements.shopName.textContent = matchedShop.name;
      elements.shopUrl.textContent = matchedShop.url;

      // Lade Rates
      const rates = await loadRates(matchedShop.id);
      displayRates(rates, elements.bestRateContent, elements.ratesList);

      showView("shop-found");
    } else {
      // Shop nicht erkannt
      elements.urlInput.value = currentUrl;

      // Prüfe Login-Status
      const loggedIn = await checkLoginStatus();

      if (loggedIn) {
        // Zeige Proposal-Formular
        await loadShopsForSelect();
        elements.loginRequired.classList.add("hidden");
        elements.createProposal.classList.remove("hidden");
      } else {
        // Zeige Login-Aufforderung
        elements.loginRequired.classList.remove("hidden");
        elements.createProposal.classList.add("hidden");
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
      throw new Error("Fehler beim Erstellen des Proposals");
    }

    return await response.json();
  } catch (error) {
    console.error("Error creating proposal:", error);
    throw error;
  }
}

// Event Listeners
elements.btnOpenWeb.addEventListener("click", () => {
  chrome.tabs.create({ url: `${API_BASE_URL}/` });
});

elements.btnLogin.addEventListener("click", () => {
  chrome.tabs.create({ url: `${API_BASE_URL}/login` });
});

elements.btnRetry.addEventListener("click", () => {
  initialize();
});

elements.proposalForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const shopId = elements.shopSelect.value;
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
    elements.proposalSuccess.classList.remove("hidden");
    elements.createProposal.classList.add("hidden");
    showView("shop-not-found");

    // Aktualisiere Cache im Background Script
    chrome.runtime.sendMessage({ action: "refreshCache" });
  } catch (error) {
    showError("Fehler beim Erstellen des Vorschlags. Bitte versuche es erneut.");
  }
});

// Initialisiere beim Laden
document.addEventListener("DOMContentLoaded", initialize);
