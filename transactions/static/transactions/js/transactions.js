"use strict";


document.addEventListener(
    "DOMContentLoaded",
    function () {
        const amountInput = document.querySelector(
            'input[name="amount"]'
        );

        if (amountInput) {
            amountInput.addEventListener(
                "input",
                function () {
                    if (Number(amountInput.value) < 0) {
                        amountInput.value = "";
                    }
                }
            );
        }

        const transactionTypeInputs =
            document.querySelectorAll(
                'input[name="transaction_type"]'
            );

        transactionTypeInputs.forEach(
            function (input) {
                input.addEventListener(
                    "change",
                    function () {
                        document.body.dataset.transactionType =
                            input.value.toLowerCase();
                    }
                );
            }
        );

        const dialog = document.getElementById(
            "deleteTransactionDialog"
        );

        const deleteForm = document.getElementById(
            "deleteTransactionForm"
        );

        const descriptionElement =
            document.getElementById(
                "delete-modal-description"
            );

        const typeElement = document.getElementById(
            "delete-modal-type"
        );

        const amountElement = document.getElementById(
            "delete-modal-amount"
        );

        const categoryElement = document.getElementById(
            "delete-modal-category"
        );

        const dateTimeElement = document.getElementById(
            "delete-modal-date-time"
        );

        const deleteButtons = document.querySelectorAll(
            ".delete-transaction-button"
        );

        const closeButtons = document.querySelectorAll(
            "[data-close-delete-dialog]"
        );

        function closeDeleteDialog() {
            if (!dialog) {
                return;
            }

            if (typeof dialog.close === "function") {
                dialog.close();
            } else {
                dialog.removeAttribute("open");
            }
        }

        function openDeleteDialog(button) {
            if (!dialog || !deleteForm) {
                return;
            }

            const transactionType =
                button.dataset.transactionType
                || "Transaction";

            const amount =
                button.dataset.transactionAmount
                || "0.00";

            const category =
                button.dataset.transactionCategory
                || "Uncategorized";

            const date =
                button.dataset.transactionDate
                || "Not recorded";

            const time =
                button.dataset.transactionTime
                || "Not recorded";

            const description =
                button.dataset.transactionDescription
                || "Transaction";

            const deleteUrl =
                button.dataset.deleteUrl;

            if (!deleteUrl) {
                return;
            }

            deleteForm.action = deleteUrl;

            if (descriptionElement) {
                descriptionElement.textContent =
                    description;
            }

            if (typeElement) {
                typeElement.textContent =
                    transactionType;
            }

            if (amountElement) {
                amountElement.textContent =
                    (
                        transactionType === "Income"
                            ? "+"
                            : "-"
                    )
                    + "₹"
                    + amount;

                amountElement.classList.remove(
                    "amount-income",
                    "amount-expense"
                );

                if (transactionType === "Income") {
                    amountElement.classList.add(
                        "amount-income"
                    );
                } else {
                    amountElement.classList.add(
                        "amount-expense"
                    );
                }
            }

            if (categoryElement) {
                categoryElement.textContent =
                    category;
            }

            if (dateTimeElement) {
                dateTimeElement.textContent =
                    date
                    + " · "
                    + time;
            }

            if (typeof dialog.showModal === "function") {
                dialog.showModal();
            } else {
                dialog.setAttribute("open", "");
            }
        }

        deleteButtons.forEach(
            function (button) {
                button.addEventListener(
                    "click",
                    function () {
                        openDeleteDialog(button);
                    }
                );
            }
        );

        closeButtons.forEach(
            function (button) {
                button.addEventListener(
                    "click",
                    function () {
                        closeDeleteDialog();
                    }
                );
            }
        );

        if (dialog) {
            dialog.addEventListener(
                "click",
                function (event) {
                    if (event.target === dialog) {
                        closeDeleteDialog();
                    }
                }
            );

            dialog.addEventListener(
                "cancel",
                function () {
                    closeDeleteDialog();
                }
            );
        }
    }
);