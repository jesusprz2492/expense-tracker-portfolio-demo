/**
 * Interacciones pequeñas y progresivas de Admin Hogar.
 *
 * No maneja datos persistentes: formularios y estado durable siempre terminan
 * en funciones PostgreSQL a través del backend.
 */

function initializeDialogs() {
  document.querySelectorAll("[data-open-dialog]").forEach((button) => {
    button.addEventListener("click", () => {
      const dialog = document.getElementById(button.dataset.openDialog);
      if (dialog) {
        dialog.showModal();
        const dateInput = dialog.querySelector('input[type="date"]');
        if (dateInput && !dateInput.value) {
          dateInput.value = new Date().toISOString().slice(0, 10);
        }
      }
    });
  });

  document.querySelectorAll("[data-close-dialog]").forEach((button) => {
    button.addEventListener("click", () => button.closest("dialog")?.close());
  });

  document.querySelectorAll("dialog").forEach((dialog) => {
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
  });
}

function initializePinGroup(group) {
  if (!group) return;
  const inputs = [...group.querySelectorAll(".pin-digit")];

  inputs.forEach((input, index) => {
    input.addEventListener("input", () => {
      input.value = input.value.replace(/\D/g, "").slice(-1);
      if (input.value && inputs[index + 1]) inputs[index + 1].focus();
    });

    input.addEventListener("keydown", (event) => {
      if (event.key === "Backspace" && !input.value && inputs[index - 1]) {
        inputs[index - 1].focus();
      }
      if (event.key === "ArrowLeft" && inputs[index - 1]) inputs[index - 1].focus();
      if (event.key === "ArrowRight" && inputs[index + 1]) inputs[index + 1].focus();
    });

    input.addEventListener("paste", (event) => {
      const digits = event.clipboardData.getData("text").replace(/\D/g, "").slice(0, inputs.length);
      if (!digits) return;
      event.preventDefault();
      digits.split("").forEach((digit, digitIndex) => {
        if (inputs[digitIndex]) inputs[digitIndex].value = digit;
      });
      inputs[Math.min(digits.length, inputs.length) - 1].focus();
    });
  });
}

function initializePinForms() {
  document.querySelectorAll("[data-pin-form]").forEach((form) => {
    const primaryGroup = form.querySelector("[data-pin-group]");
    const confirmationGroup = form.querySelector("[data-pin-confirmation-group]");
    initializePinGroup(primaryGroup);
    initializePinGroup(confirmationGroup);
    primaryGroup?.querySelector(".pin-digit")?.focus();

    form.addEventListener("submit", (event) => {
      const pin = [...primaryGroup.querySelectorAll(".pin-digit")].map((input) => input.value).join("");
      form.querySelector("[data-pin-value]").value = pin;

      if (pin.length !== 4) {
        event.preventDefault();
        primaryGroup.querySelector(".pin-digit:invalid, .pin-digit")?.focus();
        return;
      }

      if (confirmationGroup) {
        const confirmation = [...confirmationGroup.querySelectorAll(".pin-digit")]
          .map((input) => input.value)
          .join("");
        form.querySelector("[data-pin-confirmation-value]").value = confirmation;
        if (confirmation.length !== 4) event.preventDefault();
      }
    });
  });
}

function setFormValue(form, name, value) {
  const field = form?.elements.namedItem(name);
  if (field) field.value = value ?? "";
}

function initializeMovementEditor() {
  const dialog = document.getElementById("movement-edit-dialog");
  const form = dialog?.querySelector("[data-movement-edit-form]");
  if (!dialog || !form) return;

  document.querySelectorAll("[data-edit-movement]").forEach((button) => {
    button.addEventListener("click", () => {
      const values = button.dataset;
      form.action = `/movements/${values.id}`;
      setFormValue(form, "month_id", values.monthId);
      setFormValue(form, "category_id", values.categoryId);
      setFormValue(form, "kind", values.kind);
      setFormValue(form, "description", values.description);
      setFormValue(form, "amount", values.amount);
      setFormValue(form, "transaction_date", values.transactionDate);
      setFormValue(form, "note", values.note);
      setFormValue(form, "payment_method_id", values.paymentMethodId);
      setFormValue(form, "account_id", values.accountId);
      setFormValue(form, "counterparty_id", values.counterpartyId);
      dialog.showModal();
    });
  });
}

function initializePaymentMethodEditor() {
  const form = document.getElementById("payment-method-form");
  if (!form) return;
  const title = document.querySelector("[data-payment-method-title]");

  document.querySelectorAll("[data-edit-payment-method]").forEach((button) => {
    button.addEventListener("click", () => {
      setFormValue(form, "method_id", button.dataset.id);
      setFormValue(form, "name", button.dataset.name);
      setFormValue(form, "sort_order", button.dataset.sortOrder);
      if (title) title.textContent = document.documentElement.lang === "es" ? "Editar método" : "Edit method";
      form.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  });

  document.querySelector("[data-reset-payment-method]")?.addEventListener("click", () => {
    form.reset();
    setFormValue(form, "method_id", "");
    if (title) title.textContent = document.documentElement.lang === "es" ? "Nuevo método" : "New method";
  });
}

function initializeAccountEditor() {
  const form = document.getElementById("account-form");
  if (!form) return;
  const title = document.querySelector("[data-account-title]");

  document.querySelectorAll("[data-edit-account]").forEach((button) => {
    button.addEventListener("click", () => {
      setFormValue(form, "account_id", button.dataset.id);
      setFormValue(form, "name", button.dataset.name);
      setFormValue(form, "account_type", button.dataset.accountType);
      setFormValue(form, "currency", button.dataset.currency);
      setFormValue(form, "opening_balance", button.dataset.openingBalance);
      setFormValue(form, "sort_order", button.dataset.sortOrder);
      if (title) title.textContent = document.documentElement.lang === "es" ? "Editar cuenta" : "Edit account";
      form.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  });

  document.querySelector("[data-reset-account]")?.addEventListener("click", () => {
    form.reset();
    setFormValue(form, "account_id", "");
    if (title) title.textContent = document.documentElement.lang === "es" ? "Nueva cuenta" : "New account";
  });
}

function initializeContactEditor() {
  const form = document.getElementById("contact-form");
  if (!form) return;
  const title = document.querySelector("[data-contact-title]");

  document.querySelectorAll("[data-edit-contact]").forEach((button) => {
    button.addEventListener("click", () => {
      setFormValue(form, "counterparty_id", button.dataset.id);
      setFormValue(form, "party_type", button.dataset.partyType);
      setFormValue(form, "name", button.dataset.name);
      setFormValue(form, "tax_id", button.dataset.taxId);
      setFormValue(form, "email", button.dataset.email);
      setFormValue(form, "phone", button.dataset.phone);
      setFormValue(form, "notes", button.dataset.notes);
      if (title) title.textContent = document.documentElement.lang === "es" ? "Editar contacto" : "Edit contact";
      form.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  });

  document.querySelector("[data-reset-contact]")?.addEventListener("click", () => {
    form.reset();
    setFormValue(form, "counterparty_id", "");
    if (title) title.textContent = document.documentElement.lang === "es" ? "Nuevo contacto" : "New contact";
  });
}

