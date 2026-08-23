"use strict";


const analyticsState = {
    categoryChart: null,
    timelineChart: null,
    monthViewChart: null,
};


const currencyFormatter = new Intl.NumberFormat(
    "en-IN",
    {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2,
    }
);


const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
];


const chartColors = [
    "#b68155",
    "#47735c",
    "#b47b35",
    "#a6534a",
    "#8f603d",
    "#6b8f80",
    "#c49163",
    "#887d70",
];


function getElement(id) {
    return document.getElementById(id);
}


function decimalValue(value) {
    if (
        value === null
        || value === undefined
        || value === ""
    ) {
        return 0;
    }

    const parsed = Number.parseFloat(
        String(value)
            .replaceAll(",", "")
            .replace(/[₹%\s]/g, "")
    );

    return Number.isFinite(parsed)
        ? parsed
        : 0;
}


function formatCurrency(value) {
    return currencyFormatter.format(
        decimalValue(value)
    );
}


function formatPercentage(value) {
    return decimalValue(value).toFixed(2) + "%";
}


function escapeHtml(value) {
    if (
        value === null
        || value === undefined
    ) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function getCurrentMonth() {
    return new Date().getMonth() + 1;
}


function getCurrentYear() {
    return new Date().getFullYear();
}


function setText(id, value) {
    const element = getElement(id);

    if (element) {
        element.textContent = value;
    }
}


function populateYearSelect() {
    const select = getElement("year-select");

    if (!select) {
        return;
    }

    const currentYear = getCurrentYear();

    select.innerHTML = "";

    for (
        let year = currentYear - 4;
        year <= currentYear;
        year += 1
    ) {
        const option = document.createElement(
            "option"
        );

        option.value = String(year);
        option.textContent = String(year);

        select.appendChild(option);
    }

    select.value = String(currentYear);
}


function initializeMonthSelect() {
    const select = getElement("month-select");

    if (select) {
        select.value = String(
            getCurrentMonth()
        );
    }
}


function getQueryParameters() {
    const params = new URLSearchParams();

    const monthSelect = getElement(
        "month-select"
    );

    const yearSelect = getElement(
        "year-select"
    );

    params.set(
        "month",
        monthSelect
            ? monthSelect.value
            : String(getCurrentMonth())
    );

    params.set(
        "year",
        yearSelect
            ? yearSelect.value
            : String(getCurrentYear())
    );

    return params;
}


async function fetchJson(url) {
    const response = await fetch(
        url,
        {
            method: "GET",
            credentials: "same-origin",
            headers: {
                Accept: "application/json",
            },
        }
    );

    if (!response.ok) {
        let message =
            "Unable to load Analytics data.";

        try {
            const payload = await response.json();

            if (
                payload
                && payload.error
            ) {
                message = payload.error;
            }
        } catch (error) {
            message =
                "Unable to load Analytics data.";
        }

        throw new Error(message);
    }

    return response.json();
}


function showError(message) {
    const element = getElement(
        "dashboard-error"
    );

    if (!element) {
        return;
    }

    element.textContent = message;
    element.classList.remove("hidden");
}


function hideError() {
    const element = getElement(
        "dashboard-error"
    );

    if (!element) {
        return;
    }

    element.textContent = "";
    element.classList.add("hidden");
}


function updateSummary(payload) {
    const summary = payload.summary || {};

    const income = decimalValue(summary.income);
    const expense = decimalValue(summary.expense);
    const balance = decimalValue(summary.balance);

    const month = Number(summary.month);
    const year = Number(summary.year);

    const period =
        month >= 1
        && month <= 12
        && year >= 2000
            ? monthNames[month - 1]
                + " "
                + year
            : "Selected month";

    setText(
        "income-value",
        formatCurrency(income)
    );

    setText(
        "expense-value",
        formatCurrency(expense)
    );

    setText(
        "balance-value",
        formatCurrency(balance)
    );

    setText(
        "income-change",
        period
    );

    setText(
        "expense-change",
        period
    );

    setText(
        "savings-rate",
        formatPercentage(summary.savings_rate)
        + " savings rate"
    );
}


function getChartStyles() {
    const styles = getComputedStyle(
        document.documentElement
    );

    return {
        accent:
            styles
                .getPropertyValue("--accent")
                .trim()
                || "#b68155",

        income:
            styles
                .getPropertyValue("--income")
                .trim()
                || "#47735c",

        expense:
            styles
                .getPropertyValue("--expense")
                .trim()
                || "#a6534a",

        textSoft:
            styles
                .getPropertyValue("--text-soft")
                .trim()
                || "#887d70",

        border:
            styles
                .getPropertyValue("--border")
                .trim()
                || "rgba(87, 72, 60, 0.16)",

        surface:
            styles
                .getPropertyValue("--surface-raised")
                .trim()
                || "#fffaf2",
    };
}


function destroyChart(chart) {
    if (
        chart
        && typeof chart.destroy === "function"
    ) {
        chart.destroy();
    }
}


function createCategoryChart(data) {
    const canvas = getElement("category-chart");

    if (
        !canvas
        || typeof Chart === "undefined"
    ) {
        return;
    }

    const styles = getChartStyles();

    const labels = Array.isArray(data.labels)
        ? data.labels
        : [];

    const values = Array.isArray(data.values)
        ? data.values
        : [];

    destroyChart(
        analyticsState.categoryChart
    );

    const legend = getElement("category-legend");

    if (!labels.length || !values.length) {
        if (legend) {
            legend.innerHTML =
                '<div class="analytics-empty-state">'
                + "No expense categories for this month."
                + "</div>";
        }

        return;
    }

    analyticsState.categoryChart = new Chart(
        canvas,
        {
            type: "doughnut",
            data: {
                labels: labels,
                datasets: [
                    {
                        data: values,
                        backgroundColor: chartColors,
                        borderColor: styles.surface,
                        borderWidth: 3,
                        hoverOffset: 5,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "68%",
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return (
                                    context.label
                                    + ": "
                                    + formatCurrency(
                                        context.raw
                                    )
                                );
                            },
                        },
                    },
                },
            },
        }
    );

    updateCategoryLegend(labels, values);
}


function updateCategoryLegend(labels, values) {
    const container = getElement(
        "category-legend"
    );

    if (!container) {
        return;
    }

    if (!labels.length) {
        container.innerHTML =
            '<div class="analytics-empty-state">'
            + "No expense categories for this month."
            + "</div>";

        return;
    }

    container.innerHTML = labels
        .map(function (label, index) {
            const color =
                chartColors[
                    index % chartColors.length
                ];

            return (
                '<div class="analytics-legend-item">'
                + '<span class="analytics-legend-color"'
                + ' style="background: '
                + color
                + ';"></span>'
                + "<span>"
                + escapeHtml(label)
                + " · "
                + formatCurrency(values[index])
                + "</span>"
                + "</div>"
            );
        })
        .join("");
}


function createTimelineChart(data) {
    const canvas = getElement("timeline-chart");

    if (
        !canvas
        || typeof Chart === "undefined"
    ) {
        return;
    }

    const styles = getChartStyles();

    const rawLabels = Array.isArray(data.labels)
        ? data.labels
        : [];

    const labels = rawLabels.map(
        function (label) {
            const parts = String(label).split("-");

            return parts.length === 3
                ? parts[2]
                : label;
        }
    );

    const income = Array.isArray(data.income)
        ? data.income
        : [];

    const expense = Array.isArray(data.expense)
        ? data.expense
        : [];

    destroyChart(
        analyticsState.timelineChart
    );

    analyticsState.timelineChart = new Chart(
        canvas,
        {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Income",
                        data: income,
                        borderColor: styles.income,
                        backgroundColor:
                            "rgba(71, 115, 92, 0.12)",
                        borderWidth: 3,
                        fill: false,
                        tension: 0.3,
                        pointRadius: 2,
                        pointHoverRadius: 5,
                    },
                    {
                        label: "Expenses",
                        data: expense,
                        borderColor: styles.expense,
                        backgroundColor:
                            "rgba(166, 83, 74, 0.12)",
                        borderWidth: 3,
                        fill: false,
                        tension: 0.3,
                        pointRadius: 2,
                        pointHoverRadius: 5,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: "index",
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: styles.textSoft,
                            boxWidth: 11,
                            font: {
                                family: "Manrope",
                                size: 10,
                            },
                        },
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return (
                                    " "
                                    + context.dataset.label
                                    + ": "
                                    + formatCurrency(
                                        context.raw
                                    )
                                );
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        grid: {
                            display: false,
                        },
                        ticks: {
                            color: styles.textSoft,
                            maxTicksLimit: 10,
                            font: {
                                family: "Manrope",
                                size: 10,
                            },
                        },
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: styles.border,
                        },
                        ticks: {
                            color: styles.textSoft,
                            font: {
                                family: "Manrope",
                                size: 10,
                            },
                            callback: function (value) {
                                return formatCurrency(value);
                            },
                        },
                    },
                },
            },
        }
    );
}


function createMonthViewChart(data) {
    const canvas = getElement(
        "month-view-chart"
    );

    if (
        !canvas
        || typeof Chart === "undefined"
    ) {
        return;
    }

    const styles = getChartStyles();

    const labels = Array.isArray(data.labels)
        ? data.labels
        : [];

    const income = Array.isArray(data.income)
        ? data.income
        : [];

    const expense = Array.isArray(data.expense)
        ? data.expense
        : [];

    const balance = Array.isArray(data.balance)
        ? data.balance
        : [];

    destroyChart(
        analyticsState.monthViewChart
    );

    analyticsState.monthViewChart = new Chart(
        canvas,
        {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Income",
                        data: income,
                        backgroundColor: styles.income,
                        borderRadius: 5,
                        borderSkipped: false,
                        maxBarThickness: 32,
                    },
                    {
                        label: "Expenses",
                        data: expense,
                        backgroundColor: styles.expense,
                        borderRadius: 5,
                        borderSkipped: false,
                        maxBarThickness: 32,
                    },
                    {
                        label: "Balance",
                        data: balance,
                        type: "line",
                        borderColor: styles.accent,
                        backgroundColor: styles.accent,
                        borderWidth: 3,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        tension: 0.3,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: "index",
                    intersect: false,
                },
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: styles.textSoft,
                            boxWidth: 11,
                            font: {
                                family: "Manrope",
                                size: 10,
                            },
                        },
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return (
                                    " "
                                    + context.dataset.label
                                    + ": "
                                    + formatCurrency(
                                        context.raw
                                    )
                                );
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        grid: {
                            display: false,
                        },
                        ticks: {
                            color: styles.textSoft,
                            font: {
                                family: "Manrope",
                                size: 10,
                            },
                        },
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: styles.border,
                        },
                        ticks: {
                            color: styles.textSoft,
                            font: {
                                family: "Manrope",
                                size: 10,
                            },
                            callback: function (value) {
                                return formatCurrency(value);
                            },
                        },
                    },
                },
            },
        }
    );
}


function getCalendarLevel(amount, maximumAmount) {
    if (amount <= 0 || maximumAmount <= 0) {
        return 0;
    }

    const ratio = amount / maximumAmount;

    if (ratio <= 0.25) {
        return 1;
    }

    if (ratio <= 0.5) {
        return 2;
    }

    if (ratio <= 0.75) {
        return 3;
    }

    return 4;
}


function renderExpenseCalendar(data) {
    const container = getElement(
        "expense-calendar"
    );

    if (!container) {
        return;
    }

    const month = Number(data.month);
    const year = Number(data.year);

    const days = Array.isArray(data.days)
        ? data.days
        : [];

    const calendarTitle =
        month >= 1
        && month <= 12
        && year >= 2000
            ? monthNames[month - 1]
                + " "
                + year
            : "Selected month";

    setText(
        "calendar-period",
        calendarTitle
    );

    if (!days.length) {
        container.innerHTML =
            '<div class="analytics-empty-state">'
            + "No calendar data is available."
            + "</div>";

        return;
    }

    const maxExpense = Math.max.apply(
        null,
        days.map(function (day) {
            return decimalValue(day.expense);
        })
    );

    const firstWeekday = new Date(
        year,
        month - 1,
        1
    ).getDay();

    const mondayFirstOffset =
        firstWeekday === 0
            ? 6
            : firstWeekday - 1;

    const weekDays = [
        "Mon",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat",
        "Sun",
    ];

    let html = weekDays
        .map(function (dayName) {
            return (
                '<div class="analytics-calendar-weekday">'
                + dayName
                + "</div>"
            );
        })
        .join("");

    for (
        let index = 0;
        index < mondayFirstOffset;
        index += 1
    ) {
        html += '<div class="analytics-calendar-empty"></div>';
    }

    html += days
        .map(function (day) {
            const amount = decimalValue(
                day.expense
            );

            const count = Number(
                day.transaction_count
            ) || 0;

            const level = getCalendarLevel(
                amount,
                maxExpense
            );

            const dateParts = String(day.date).split(
                "-"
            );

            const dayNumber =
                dateParts.length === 3
                    ? Number(dateParts[2])
                    : "";

            const title = amount > 0
                ? (
                    day.date
                    + ": "
                    + formatCurrency(amount)
                    + " across "
                    + count
                    + " expense transaction"
                    + (count === 1 ? "" : "s")
                )
                : (
                    day.date
                    + ": No expense recorded"
                );

            const amountHtml = amount > 0
                ? (
                    '<span class="analytics-calendar-day-amount">'
                    + formatCurrency(amount)
                    + "</span>"
                )
                : "";

            const countHtml = count > 0
                ? (
                    '<span class="analytics-calendar-day-count">'
                    + count
                    + " transaction"
                    + (count === 1 ? "" : "s")
                    + "</span>"
                )
                : "";

            return (
                '<div class="analytics-calendar-day '
                + "calendar-level-"
                + level
                + (amount > 0 ? " has-expense" : "")
                + '" title="'
                + escapeHtml(title)
                + '">'
                + '<span class="analytics-calendar-day-number">'
                + dayNumber
                + "</span>"
                + amountHtml
                + countHtml
                + "</div>"
            );
        })
        .join("");

    container.innerHTML = html;
}


async function loadAnalytics() {
    hideError();

    const params = getQueryParameters();

    const dashboardUrl =
        "/analytics/api/dashboard/?"
        + params.toString();

    const categoryUrl =
        "/analytics/charts/categories/?"
        + params.toString();

    const timelineUrl =
        "/analytics/charts/timeline/?"
        + params.toString();

    const calendarUrl =
        "/analytics/charts/expense-calendar/?"
        + params.toString();

    const monthViewParams = new URLSearchParams(
        params
    );

    monthViewParams.set("months", "6");

    const monthViewUrl =
        "/analytics/charts/month-view/?"
        + monthViewParams.toString();

    const results = await Promise.all([
        fetchJson(dashboardUrl),
        fetchJson(categoryUrl),
        fetchJson(timelineUrl),
        fetchJson(monthViewUrl),
        fetchJson(calendarUrl),
    ]);

    updateSummary(results[0]);

    createCategoryChart(results[1]);

    createTimelineChart(results[2]);

    createMonthViewChart(results[3]);

    renderExpenseCalendar(results[4]);

    setText(
        "last-updated",
        "Updated "
        + new Date().toLocaleTimeString(
            "en-IN",
            {
                hour: "2-digit",
                minute: "2-digit",
            }
        )
    );
}


function setButtonsLoading(isLoading) {
    const applyButton = getElement(
        "apply-filters"
    );

    const refreshButton = getElement(
        "refresh-dashboard"
    );

    if (applyButton) {
        applyButton.disabled = isLoading;
    }

    if (refreshButton) {
        refreshButton.disabled = isLoading;
    }
}


async function refreshAnalytics() {
    setButtonsLoading(true);

    try {
        await loadAnalytics();
    } catch (error) {
        showError(
            error && error.message
                ? error.message
                : "Unable to load Analytics data."
        );
    } finally {
        setButtonsLoading(false);
    }
}


function bindEvents() {
    const applyButton = getElement(
        "apply-filters"
    );

    const refreshButton = getElement(
        "refresh-dashboard"
    );

    if (applyButton) {
        applyButton.addEventListener(
            "click",
            refreshAnalytics
        );
    }

    if (refreshButton) {
        refreshButton.addEventListener(
            "click",
            refreshAnalytics
        );
    }
}


document.addEventListener(
    "DOMContentLoaded",
    function () {
        populateYearSelect();

        initializeMonthSelect();

        bindEvents();

        refreshAnalytics();
    }
);