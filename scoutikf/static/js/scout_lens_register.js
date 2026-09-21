(() => {
  "use strict";

  const root = document.getElementById("scoutlens-registration");
  if (!root) return;

  const form = document.getElementById("scoutlens-form");
  const payButton = document.getElementById("pay-button");
  const message = document.getElementById("payment-message");
  const result = document.getElementById("payment-result");
  const recovery = document.getElementById("payment-recovery");
  const reconcileButton = document.getElementById("reconcile-button");
  const resumeButton = document.getElementById("resume-button");
  const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;
  const storageKey = "scoutlensPaymentSession";
  const positionInput = document.getElementById("id_position");
  const affiliateInput = document.getElementById("id_affiliate_code");
  const affiliateBanner = document.getElementById("affiliate-banner");
  const affiliateMessage = document.getElementById("affiliate-message");
  let paymentSession = null;
  let currentFinalAmount = document.getElementById("display-final-fee").textContent;

  const setMessage = (text, kind = "error") => {
    message.textContent = text || "";
    message.className = `slr-message${text ? ` is-${kind}` : ""}`;
  };

  const setBusy = (busy, label = "Register & Pay") => {
    payButton.disabled = busy;
    document.getElementById("pay-button-label").textContent = busy ? label : `Register & Pay ₹${currentFinalAmount}`;
  };

  const post = async (url, data) => {
    const body = new FormData();
    Object.entries(data).forEach(([key, value]) => body.append(key, value == null ? "" : value));
    const response = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "X-CSRFToken": csrfToken, "X-Requested-With": "XMLHttpRequest" },
      body,
    });
    let payload;
    try { payload = await response.json(); }
    catch (_) { payload = { ok: false, message: "The server returned an unexpected response." }; }
    if (!response.ok && response.status !== 202) throw Object.assign(new Error(payload.message || "Request failed."), { payload });
    return payload;
  };

  const clearErrors = () => {
    form.querySelectorAll(".slr-error").forEach((node) => { node.textContent = ""; });
    form.querySelectorAll("[aria-invalid]").forEach((node) => node.removeAttribute("aria-invalid"));
  };

  const refreshQuote = async () => {
    if (!positionInput.value) return;
    try {
      const quote = await post(root.dataset.quoteUrl, {
        position: positionInput.value,
        affiliate_code: affiliateInput.value,
      });
      document.getElementById("display-final-fee").textContent = Number(quote.final_amount).toFixed(2);
      currentFinalAmount = Number(quote.final_amount).toFixed(2);
      document.getElementById("pay-button-label").textContent = `Register & Pay ₹${currentFinalAmount}`;
      document.getElementById("display-discount").textContent = Number(quote.discount_amount).toFixed(2);
      document.getElementById("discount-summary").hidden = Number(quote.discount_amount) <= 0;
      if (affiliateBanner && affiliateMessage && affiliateInput.value) {
        affiliateBanner.classList.remove("is-invalid");
        affiliateMessage.textContent = quote.affiliate_name
          ? `Affiliate code ${affiliateInput.value.toUpperCase()} applied from ${quote.affiliate_name}.`
          : `Affiliate code ${affiliateInput.value.toUpperCase()} applied.`;
      }
      setMessage("");
    } catch (error) {
      if (affiliateBanner) affiliateBanner.classList.add("is-invalid");
      if (affiliateMessage) affiliateMessage.textContent = error.message;
      setMessage(error.message);
    }
  };

  const showErrors = (errors = {}) => {
    Object.entries(errors).forEach(([field, entries]) => {
      const error = document.getElementById(`error-${field}`);
      const input = document.getElementById(`id_${field}`);
      if (error) error.textContent = entries.join(" ");
      if (input) input.setAttribute("aria-invalid", "true");
    });
  };

  const saveSession = (data) => {
    paymentSession = data;
    sessionStorage.setItem(storageKey, JSON.stringify(data));
    recovery.hidden = false;
  };

  const complete = (data) => {
    form.hidden = true;
    recovery.hidden = true;
    result.hidden = false;
    document.getElementById("result-message").textContent = data.message || "Your payment has been verified and your ScoutLens registration is confirmed.";
    document.getElementById("registration-reference").textContent = data.registration_id || paymentSession?.registration_id || "";
    sessionStorage.removeItem(storageKey);
  };

  const reportFailure = async (error) => {
    if (!paymentSession) return;
    const metadata = error?.metadata || {};
    try {
      await post(root.dataset.failedUrl, {
        payment_token: paymentSession.payment_token,
        code: error?.code || "",
        description: error?.description || "Payment was not completed.",
        source: error?.source || "checkout",
        reason: error?.reason || "",
        payment_id: metadata.payment_id || "",
      });
    } catch (_) { /* Reconciliation remains available even if failure logging is interrupted. */ }
  };

  const openCheckout = async (session) => {
    if (typeof window.Razorpay !== "function") throw new Error("Razorpay Checkout could not load. Check your connection and try again.");
    const order = await post(root.dataset.orderUrl, { payment_token: session.payment_token });
    if (order.already_paid) return complete({ registration_id: session.registration_id, message: "This registration is already paid and verified." });

    const checkout = new window.Razorpay({
      key: root.dataset.keyId,
      amount: order.amount_paise,
      currency: order.currency,
      order_id: order.order_id,
      name: "IKF ScoutLens",
      description: "ScoutLens player registration",
      prefill: { name: session.player_name, contact: session.mobile },
      theme: { color: "#10b981" },
      modal: {
        confirm_close: true,
        ondismiss: () => {
          setBusy(false);
          setMessage("Payment window closed. If money was deducted, use Check payment status.", "info");
          recovery.hidden = false;
        },
      },
      handler: async (response) => {
        setMessage("Verifying your payment securely…", "info");
        try {
          const verified = await post(root.dataset.verifyUrl, {
            payment_token: session.payment_token,
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          if (verified.paid) complete(verified);
          else {
            setMessage(verified.message || "Payment verification is pending.", "info");
            recovery.hidden = false;
          }
        } catch (error) {
          setMessage(error.message, "info");
          recovery.hidden = false;
        } finally { setBusy(false); }
      },
    });
    checkout.on("payment.failed", async (response) => {
      await reportFailure(response.error);
      setBusy(false);
      setMessage(response.error?.description || "Payment was not completed. You can safely check its status below.");
      recovery.hidden = false;
    });
    checkout.open();
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearErrors();
    setMessage("");
    setBusy(true, "Preparing secure payment…");
    try {
      const start = await post(root.dataset.startUrl, Object.fromEntries(new FormData(form).entries()));
      const session = {
        registration_id: start.registration_id,
        payment_token: start.payment_token,
        player_name: start.player_name,
        mobile: start.mobile,
      };
      saveSession(session);
      await openCheckout(session);
    } catch (error) {
      showErrors(error.payload?.errors);
      setMessage(error.message);
      setBusy(false);
    }
  });

  positionInput.addEventListener("change", refreshQuote);

  reconcileButton.addEventListener("click", async () => {
    if (!paymentSession) return;
    reconcileButton.disabled = true;
    setMessage("Checking Razorpay for a captured payment…", "info");
    try {
      const status = await post(root.dataset.reconcileUrl, { payment_token: paymentSession.payment_token });
      if (status.paid) complete(status);
      else setMessage(status.message || "No captured payment was found yet.", "info");
    } catch (error) { setMessage(error.message); }
    finally { reconcileButton.disabled = false; }
  });

  resumeButton.addEventListener("click", async () => {
    if (!paymentSession) return;
    resumeButton.disabled = true;
    setMessage("Reopening your existing secure payment order…", "info");
    try { await openCheckout(paymentSession); }
    catch (error) { setMessage(error.message); }
    finally { resumeButton.disabled = false; }
  });

  try {
    const saved = JSON.parse(sessionStorage.getItem(storageKey));
    if (saved?.payment_token) {
      paymentSession = saved;
      recovery.hidden = false;
    }
  } catch (_) { sessionStorage.removeItem(storageKey); }
})();
