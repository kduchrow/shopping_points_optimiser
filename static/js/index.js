// index.js: Dynamisches Nachladen der Shop-Liste für index.html

document.addEventListener("DOMContentLoaded", function () {
  const shopSelect = document.getElementById("shop-select");
  let choicesInstance = null;
  let lastQuery = "";
  let debounceTimeout = null;

  // Choices.js initialisieren
  if (shopSelect) {
    choicesInstance = new Choices(shopSelect, {
      searchEnabled: true,
      searchPlaceholderValue: "Shop suchen oder tippen...",
      itemSelectText: "",
      noResultsText: "Keine Shops gefunden",
      noChoicesText: "Keine Shops verfügbar",
      maxItemCount: 100,
      shouldSort: true,
      searchResultLimit: 100,
      renderChoiceLimit: 100,
      removeItemButton: false,
      allowHTML: false,
    });
    console.log("Choices initialisiert", choicesInstance);

    // Listener auf das Suchfeld setzen, sobald das Dropdown geöffnet wird
    function attachSearchListener() {
      // Choices.js erzeugt ein <input type="text" class="choices__input choices__input--cloned">
      const input = document.querySelector(".choices__input--cloned");
      console.log("attachSearchListener aufgerufen", input);
      if (!input) return;
      if (input.dataset.listenerAttached) return;
      input.addEventListener("keyup", function () {
        console.log("Keyup im Suchfeld", input.value);
        const query = input.value.trim();
        if (query.length < 2) {
          choicesInstance.clearChoices();
          choicesInstance.setChoices(
            [{ value: "", label: "-- Shop auswählen --", selected: true, disabled: true }],
            "value",
            "label",
            false,
          );
          return;
        }
        if (query === lastQuery) return;
        lastQuery = query;
        if (debounceTimeout) clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
          fetch(`/shop_names?q=${encodeURIComponent(query)}`)
            .then((resp) => resp.json())
            .then((data) => {
              const choices = data.map((shop) => ({ value: shop.id, label: shop.name }));
              if (choices.length === 0) {
                choices.push({ value: "", label: "Keine Shops gefunden", disabled: true });
              }
              choicesInstance.clearChoices();
              choicesInstance.setChoices(choices, "value", "label", false);
            });
        }, 200);
      });
      input.dataset.listenerAttached = "true";
    }

    // Globaler keyup-Listener zum Debuggen
    document.addEventListener("keyup", function (e) {
      console.log("Global keyup:", e.target, e.target.className, e.target.value);
    });
    // Choices.js Event: Jedes Mal, wenn das Dropdown geöffnet wird, Listener setzen
    shopSelect.addEventListener("showDropdown", attachSearchListener);
  }
});
