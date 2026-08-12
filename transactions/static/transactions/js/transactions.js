document.addEventListener("DOMContentLoaded", () => {
    const amountInput = document.querySelector(
        'input[name="amount"]'
    );

    amountInput?.addEventListener("input", () => {
        if (Number(amountInput.value) < 0) {
            amountInput.value = "";
        }
    });

    const transactionTypeInputs = document.querySelectorAll(
        'input[name="transaction_type"]'
    );

    transactionTypeInputs.forEach((input) => {
        input.addEventListener("change", () => {
            document.body.dataset.transactionType =
                input.value.toLowerCase();
        });
    });
});