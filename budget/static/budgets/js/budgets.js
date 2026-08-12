document.addEventListener("DOMContentLoaded", () => {
    const progressBars = document.querySelectorAll(
        ".budget-progress-bar"
    );

    progressBars.forEach((bar) => {
        const progress = Number(
            bar.dataset.progress || 0
        );

        const safeProgress = Math.min(
            Math.max(progress, 0),
            100
        );

        requestAnimationFrame(() => {
            bar.style.width = `${safeProgress}%`;
        });
    });

    const budgetLimitInput = document.querySelector(
        'input[name="budget_limit"]'
    );

    budgetLimitInput?.addEventListener("input", () => {
        if (Number(budgetLimitInput.value) < 0) {
            budgetLimitInput.value = "";
        }
    });

    const startDateInput = document.querySelector(
        'input[name="start_date"]'
    );

    const endDateInput = document.querySelector(
        'input[name="end_date"]'
    );

    const updateMonthEnd = () => {
        if (!startDateInput || !endDateInput) {
            return;
        }

        if (!startDateInput.value) {
            return;
        }

        const startDate = new Date(
            `${startDateInput.value}T00:00:00`
        );

        if (Number.isNaN(startDate.getTime())) {
            return;
        }

        const year = startDate.getFullYear();
        const month = startDate.getMonth();

        const lastDay = new Date(
            year,
            month + 1,
            0
        ).getDate();

        const monthEnd = [
            year,
            String(month + 1).padStart(2, "0"),
            String(lastDay).padStart(2, "0"),
        ].join("-");

        endDateInput.value = monthEnd;
    };

    startDateInput?.addEventListener(
        "change",
        updateMonthEnd
    );

    updateMonthEnd();
});