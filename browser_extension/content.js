/**
 * Content Script - läuft auf jeder Webseite
 * Kann bei Bedarf erweitert werden für direkte DOM-Interaktionen
 */

// Sende aktuelle URL an Background Script
chrome.runtime.sendMessage({
  action: "checkCurrentPage",
  url: window.location.href,
});

console.log("Shopping Points Optimiser: Content script loaded");
