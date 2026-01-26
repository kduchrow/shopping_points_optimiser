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

  fetch("/evaluate", {
    method: "POST",
    body: formData,
    headers: { "X-Requested-With": "XMLHttpRequest" },
  })
    .then((response) => response.text())
    .then((html) => {
      const oldResults = document.getElementById("results-list");
      if (oldResults && html) {
        oldResults.innerHTML = html;
      }
    })
    .catch((err) => {
      console.error("Fehler bei der Neuberechnung:", err);
    });
}

function toggleMode(sortBy, evt) {
  const resultsList = document.getElementById("results-list");
  if (!resultsList) return;

  const items = Array.from(resultsList.querySelectorAll(":scope > li"));

  // Remove active class from all toggle buttons
  document.querySelectorAll(".toggle-switch-btn").forEach((btn) => btn.classList.remove("active"));
  if (evt?.target) {
    evt.target.classList.add("active");
  }

  // Sort items by selected mode
  items.sort((a, b) => {
    let valueA = 0;
    let valueB = 0;
    if (sortBy === "base") {
      valueA = parseFloat(a.dataset.baseValue) || 0;
      valueB = parseFloat(b.dataset.baseValue) || 0;
    } else {
      valueA = parseFloat(a.dataset.couponValue) || 0;
      valueB = parseFloat(b.dataset.couponValue) || 0;
    }
    return valueB - valueA;
  });

  // Re-insert sorted items
  resultsList.innerHTML = "";
  items.forEach((item) => resultsList.appendChild(item));
}

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
