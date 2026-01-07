function sortResults(sortBy, evt) {
  const resultsList = document.getElementById("results-list");
  if (!resultsList) return;
  const items = Array.from(resultsList.querySelectorAll("li"));

  document.querySelectorAll(".sort-btn").forEach((btn) => btn.classList.remove("active"));
  if (evt?.target) {
    evt.target.classList.add("active");
  }

  items.sort((a, b) => {
    let valueA;
    let valueB;
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
