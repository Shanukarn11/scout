(() => {
  "use strict";

  const overlay = document.getElementById("scoutlens-notify");
  if (!overlay) return;

  const form = document.getElementById("notify-form");
  const closeButton = document.getElementById("notify-close");
  const positionInput = document.getElementById("notify-position");
  const positionLabel = document.getElementById("notify-position-label");
  const message = document.getElementById("notify-message");
  const submitButton = form.querySelector("button[type=submit]");
  const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;

  const clearErrors = () => {
    form.querySelectorAll(".mfk-notify-error").forEach((node) => { node.textContent = ""; });
    message.textContent = "";
    message.className = "mfk-notify-message";
  };

  const open = (button) => {
    clearErrors();
    positionInput.value = button.dataset.notifyPosition;
    positionLabel.textContent = button.dataset.notifyLabel;
    overlay.hidden = false;
    document.body.style.overflow = "hidden";
    document.getElementById("notify-name").focus();
  };

  const close = () => {
    overlay.hidden = true;
    document.body.style.overflow = "";
  };

  document.querySelectorAll("[data-notify-position]").forEach((button) => {
    button.addEventListener("click", () => open(button));
  });
  closeButton.addEventListener("click", close);
  overlay.addEventListener("click", (event) => { if (event.target === overlay) close(); });
  document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !overlay.hidden) close(); });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearErrors();
    submitButton.disabled = true;
    try {
      const response = await fetch(overlay.dataset.submitUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrfToken, "X-Requested-With": "XMLHttpRequest" },
        body: new FormData(form),
      });
      let payload;
      try { payload = await response.json(); }
      catch (_) { payload = { ok: false, message: "The server returned an unexpected response." }; }

      if (payload.errors) {
        Object.entries(payload.errors).forEach(([field, errors]) => {
          const node = document.getElementById(`notify-error-${field}`);
          if (node) node.textContent = errors.join(" ");
        });
      }
      message.textContent = payload.message || (response.ok ? "Saved." : "Please try again.");
      message.classList.toggle("is-success", response.ok && payload.ok);
      if (response.ok && payload.ok) {
        form.querySelectorAll("input:not([type=hidden])").forEach((input) => { input.value = ""; });
      }
    } catch (_) {
      message.textContent = "We could not save your request. Check your connection and try again.";
    } finally {
      submitButton.disabled = false;
    }
  });
})();
