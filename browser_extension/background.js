/**
 * Background Service Worker für Shopping Points Optimiser Extension
 * Verwaltet die Shop-Erkennung und Badge-Updates
 */

// API Base URL - ändern für Production
const API_BASE_URL = "http://localhost:5000";

// Shop-Daten Cache
let shopsCache = [];
let lastFetchTime = 0;
const CACHE_DURATION = 5 * 60 * 1000; // 5 Minuten

/**
 * Lädt alle Shops von der API
 */
async function fetchShops() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/shops`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    shopsCache = data.shops || [];
    lastFetchTime = Date.now();
    return shopsCache;
  } catch (error) {
    console.error("Error fetching shops:", error);
    return [];
  }
}

/**
 * Gibt die Shop-Liste zurück (aus Cache oder neu geladen)
 */
async function getShops() {
  if (Date.now() - lastFetchTime > CACHE_DURATION || shopsCache.length === 0) {
    return await fetchShops();
  }
  return shopsCache;
}

/**
 * Extrahiert die Top-Level-Domain (z.B. example.com von www.example.com)
 */
function extractTLD(hostname) {
  const parts = hostname.split(".");
  if (parts.length >= 2) {
    // Nimm die letzten 2 Teile (domain.tld)
    return parts.slice(-2).join(".");
  }
  return hostname;
}

/**
 * Prüft ob die aktuelle URL einem bekannten Shop entspricht
 */
function matchShop(url, shops) {
  try {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname.toLowerCase();
    const tld = extractTLD(hostname);

    for (const shop of shops) {
      // Prüfe Shop-URL
      if (shop.url) {
        try {
          const shopUrl = new URL(shop.url);
          const shopTld = extractTLD(shopUrl.hostname.toLowerCase());
          if (tld === shopTld) {
            return shop;
          }
        } catch (e) {
          // Ignore invalid shop URLs
        }
      }

      // Prüfe alternative URLs
      if (shop.alternative_urls && Array.isArray(shop.alternative_urls)) {
        for (const altUrl of shop.alternative_urls) {
          try {
            const altUrlObj = new URL(altUrl);
            const altTld = extractTLD(altUrlObj.hostname.toLowerCase());
            if (tld === altTld) {
              return shop;
            }
          } catch (e) {
            // Ignore invalid URLs
          }
        }
      }
    }

    return null;
  } catch (error) {
    console.error("Error matching shop:", error);
    return null;
  }
}

/**
 * Aktualisiert das Badge für einen Tab
 */
async function updateBadge(tabId, url) {
  const shops = await getShops();
  const matchedShop = matchShop(url, shops);

  if (matchedShop) {
    // Zeige Ausrufezeichen wenn Shop erkannt wurde
    chrome.action.setBadgeText({ tabId, text: "!" });
    chrome.action.setBadgeBackgroundColor({ tabId, color: "#4CAF50" });

    // Speichere den erkannten Shop für das Popup
    chrome.storage.local.set({ [`shop_${tabId}`]: matchedShop });
  } else {
    // Kein Badge wenn Shop nicht erkannt
    chrome.action.setBadgeText({ tabId, text: "" });
    chrome.storage.local.remove([`shop_${tabId}`]);
  }
}

// Event Listener: Tab-Updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url) {
    updateBadge(tabId, tab.url);
  }
});

// Event Listener: Tab-Wechsel
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  const tab = await chrome.tabs.get(activeInfo.tabId);
  if (tab.url) {
    updateBadge(activeInfo.tabId, tab.url);
  }
});

// Event Listener: Extension Installation
chrome.runtime.onInstalled.addListener(() => {
  console.log("Shopping Points Optimiser Extension installed");
  fetchShops(); // Initial fetch
});

// Message Handler für Kommunikation mit Popup/Content Scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getShops") {
    getShops().then((shops) => sendResponse({ shops }));
    return true; // Async response
  }

  if (request.action === "matchShop") {
    getShops().then((shops) => {
      const matched = matchShop(request.url, shops);
      sendResponse({ shop: matched });
    });
    return true;
  }

  if (request.action === "refreshCache") {
    fetchShops().then((shops) => sendResponse({ shops }));
    return true;
  }
});
