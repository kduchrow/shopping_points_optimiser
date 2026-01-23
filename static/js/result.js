/* COUPON FUNCTIONALITY COMMENTED OUT
// AJAX recalculation for coupon selection
document.addEventListener("DOMContentLoaded", function () {
  const couponForm = document.getElementById("coupon-selection-form");
  if (couponForm) {
    couponForm.addEventListener("change", function (e) {
      if (e.target.classList.contains("coupon-tickbox")) {
        recalculateResults();
      }
    });
  }
});

function recalculateResults() {
  const couponForm = document.getElementById("coupon-selection-form");
  if (!couponForm) return;
  const formData = new FormData(couponForm);
  // Add shop, amount, and mode fields (hidden in form or fallback from page)
  if (!formData.has("shop")) {
    const shopInput = document.querySelector('input[name="shop"]');
    if (shopInput) formData.append("shop", shopInput.value);
  }
  if (!formData.has("amount")) {
    const amountInput = document.querySelector('input[name="amount"]');
    if (amountInput) formData.append("amount", amountInput.value);
  }
  if (!formData.has("mode")) {
    const modeInput = document.querySelector('input[name="mode"]');
    if (modeInput) formData.append("mode", modeInput.value);
    else formData.append("mode", "shopping");
  }

  fetch("/evaluate", {
    method: "POST",
    body: formData,
    headers: { "X-Requested-With": "XMLHttpRequest" },
  })
    .then((response) => response.text())
    .then((html) => {
      // Replace the results list and possibly other dynamic content
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      const newResults = doc.getElementById("results-list");
      const oldResults = document.getElementById("results-list");
      if (newResults && oldResults) {
        oldResults.innerHTML = newResults.innerHTML;
      }
      // Optionally update other dynamic sections (warnings, etc.)
    })
    .catch((err) => {
      console.error("Fehler bei der Neuberechnung:", err);
    });
}
function sortResults(sortBy, evt) {
  const resultsList = document.getElementById("results-list");
  if (!resultsList) return;
  const items = Array.from(resultsList.querySelectorAll(":scope > li"));

  document.querySelectorAll(".sort-btn, .mode-btn").forEach((btn) => btn.classList.remove("active"));
  if (evt?.target) {
    evt.target.classList.add("active");
  }

  items.sort((a, b) => {
    let valueA = 0;
    let valueB = 0;
    if (sortBy === "base") {
      valueA = parseFloat(a.dataset.baseValue);
      valueB = parseFloat(b.dataset.baseValue);
    } else {
      valueA = parseFloat(a.dataset.couponValue);
      valueB = parseFloat(b.dataset.couponValue);
    }
    return valueB - valueA;
  });

  resultsList.innerHTML = "";
  items.forEach((item) => resultsList.appendChild(item));
}
*/

function openProposalModal(proposalId, shopName, reason, sourceUrl) {
  const modal = document.getElementById("proposalModal");
  if (!modal) return;
  document.getElementById("modalShopName").textContent = shopName;
  document.getElementById("modalReason").textContent = reason;
  const sourceLink = document.getElementById("modalSourceLink");
  if (sourceLink) {
    if (sourceUrl) {
      sourceLink.href = sourceUrl;
      sourceLink.style.display = "inline";
    } else {
      sourceLink.style.display = "none";
    }
  }
  const reviewBtn = document.getElementById("reviewBtn");
  if (reviewBtn)
    reviewBtn.onclick = () => {
      window.location.href = `/review-scraper-proposal/${proposalId}`;
    };
  modal.style.display = "block";
}

function closeProposalModal() {
  const modal = document.getElementById("proposalModal");
  if (modal) modal.style.display = "none";
}

window.onclick = (evt) => {
  const modal = document.getElementById("proposalModal");
  if (evt.target === modal) {
    modal.style.display = "none";
  }
};
