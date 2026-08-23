"use strict";


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


function getElement(id) {
    return document.getElementById(id);
}


function decimalValue(value) {
    if (typeof value === "number") {
        return Number.isFinite(value)
            ? value
            : 0;
    }

    if (
        value === null
        || value === undefined
        || value === ""
    ) {
        return 0;
    }

    const normalized = String(value)
        .replaceAll(",", "")
        .replace(/[₹%\s]/g, "");

    const parsed = Number.parseFloat(normalized);

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


function getObjectValue(
    object,
    key,
    defaultValue
) {
    if (
        !object
        || typeof object !== "object"
    ) {
        return defaultValue;
    }

    if (
        object[key] === undefined
        || object[key] === null
    ) {
        return defaultValue;
    }

    return object[key];
}


function getMetricValue(
    object,
    keys,
    defaultValue
) {
    const fallback =
        defaultValue === undefined
            ? 0
            : defaultValue;

    if (
        !object
        || typeof object !== "object"
    ) {
        return fallback;
    }

    for (
        let index = 0;
        index < keys.length;
        index += 1
    ) {
        const key = keys[index];

        if (
            object[key] !== undefined
            && object[key] !== null
        ) {
            return object[key];
        }
    }

    return fallback;
}


function normalizeList(value) {
    return Array.isArray(value)
        ? value
        : [];
}


function setText(id, value) {
    const element = getElement(id);

    if (element) {
        element.textContent = value;
    }
}


function populateYears() {
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


function initializePeriod() {
    const monthSelect = getElement(
        "month-select"
    );

    if (monthSelect) {
        monthSelect.value = String(
            getCurrentMonth()
        );
    }
}


function showError(message) {
    const element = getElement(
        "summary-error"
    );

    if (!element) {
        return;
    }

    element.textContent =
        message || "Unable to load summary.";

    element.classList.remove("hidden");
}


function hideError() {
    const element = getElement(
        "summary-error"
    );

    if (!element) {
        return;
    }

    element.textContent = "";
    element.classList.add("hidden");
}


function getSummaryParameters() {
    const params = new URLSearchParams();

    const monthSelect = getElement(
        "month-select"
    );

    const yearSelect = getElement(
        "year-select"
    );

    const month = monthSelect
        ? monthSelect.value
        : getCurrentMonth();

    const year = yearSelect
        ? yearSelect.value
        : getCurrentYear();

    params.set(
        "month",
        String(month)
    );

    params.set(
        "year",
        String(year)
    );

    return params;
}


async function fetchJson(url, errorMessage) {
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
        let message = errorMessage;

        try {
            const payload = await response.json();

            if (
                payload
                && payload.error
            ) {
                message = payload.error;
            }
        } catch (error) {
            message = errorMessage;
        }

        throw new Error(message);
    }

    return response.json();
}


async function fetchSummary() {
    const params = getSummaryParameters();

    return fetchJson(
        "/ai-summary/api/?"
        + params.toString(),
        "Unable to generate summary."
    );
}


async function fetchForecastData() {
    const params = new URLSearchParams();

    params.set("months", "12");

    return fetchJson(
        "/analytics/forecast/features/?"
        + params.toString(),
        "Unable to load forecast data."
    );
}


function getPayloadMetrics(payload) {
    if (
        !payload
        || typeof payload !== "object"
    ) {
        return {};
    }

    if (
        payload.metrics
        && typeof payload.metrics === "object"
    ) {
        return payload.metrics;
    }

    if (
        payload.summary
        && payload.summary.metrics
        && typeof payload.summary.metrics === "object"
    ) {
        return payload.summary.metrics;
    }

    return {};
}


function getSummaryMetrics(payload) {
    const metrics = getPayloadMetrics(payload);

    if (
        metrics.summary
        && typeof metrics.summary === "object"
    ) {
        return metrics.summary;
    }

    return metrics;
}


function getPayloadInsights(payload) {
    if (
        payload
        && Array.isArray(payload.insights)
    ) {
        return payload.insights;
    }

    if (
        payload
        && payload.summary
        && Array.isArray(payload.summary.insights)
    ) {
        return payload.summary.insights;
    }

    return [];
}


function getPayloadRecommendations(payload) {
    if (
        payload
        && Array.isArray(payload.recommendations)
    ) {
        return payload.recommendations;
    }

    if (
        payload
        && payload.summary
        && Array.isArray(
            payload.summary.recommendations
        )
    ) {
        return payload.summary.recommendations;
    }

    return [];
}


function getSafeInsightType(type) {
    if (type === "positive") {
        return "positive";
    }

    if (type === "warning") {
        return "warning";
    }

    return "neutral";
}


function getSafePriority(priority) {
    if (priority === "high") {
        return "warning";
    }

    if (priority === "low") {
        return "positive";
    }

    return "neutral";
}


function getBudgetStatusDetails(budget) {
    const status = getObjectValue(
        budget,
        "status",
        ""
    );

    const isOverBudget = getObjectValue(
        budget,
        "is_over_budget",
        false
    );

    if (
        isOverBudget
        || status === "over_budget"
    ) {
        return {
            cssClass: "over-budget",
            label: "Over budget",
        };
    }

    if (status === "at_limit") {
        return {
            cssClass: "at-limit",
            label: "At limit",
        };
    }

    if (status === "near_limit") {
        return {
            cssClass: "near-limit",
            label: "Near limit",
        };
    }

    return {
        cssClass: "within-budget",
        label: "Within budget",
    };
}


function renderInitialMetrics() {
    const income = getElement("metric-income");
    const expense = getElement("metric-expense");
    const balance = getElement("metric-balance");
    const savingsRate = getElement(
        "metric-savings-rate"
    );

    if (
        income
        && !income.textContent.trim()
    ) {
        income.textContent = formatCurrency(0);
    }

    if (
        expense
        && !expense.textContent.trim()
    ) {
        expense.textContent = formatCurrency(0);
    }

    if (
        balance
        && !balance.textContent.trim()
    ) {
        balance.textContent = formatCurrency(0);
    }

    if (
        savingsRate
        && !savingsRate.textContent.trim()
    ) {
        savingsRate.textContent =
            formatPercentage(0);
    }
}


function renderSummaryText(payload) {
    const month = Number(
        getObjectValue(
            payload,
            "month",
            getCurrentMonth()
        )
    );

    const year = Number(
        getObjectValue(
            payload,
            "year",
            getCurrentYear()
        )
    );

    const validMonth =
        month >= 1 && month <= 12
            ? month
            : getCurrentMonth();

    const validYear =
        year >= 2000
            ? year
            : getCurrentYear();

    let summaryText = getObjectValue(
        payload,
        "summary_text",
        ""
    );

    if (
        !summaryText
        && payload
        && payload.summary
    ) {
        summaryText = getObjectValue(
            payload.summary,
            "summary_text",
            ""
        );
    }

    setText(
        "summary-period",
        monthNames[validMonth - 1]
        + " "
        + validYear
    );

    setText(
        "summary-text",
        summaryText || "No summary available."
    );
}


function renderMetrics(payload) {
    const summary = getSummaryMetrics(payload);

    const income = decimalValue(
        getMetricValue(
            summary,
            [
                "income",
                "total_income",
                "totalIncome",
            ],
            0
        )
    );

    const expense = decimalValue(
        getMetricValue(
            summary,
            [
                "expense",
                "expenses",
                "total_expense",
                "total_expenses",
                "totalExpense",
                "totalExpenses",
            ],
            0
        )
    );

    const calculatedBalance = income - expense;

    const balance = decimalValue(
        getMetricValue(
            summary,
            [
                "balance",
                "net_balance",
                "netBalance",
            ],
            calculatedBalance
        )
    );

    const calculatedSavingsRate =
        income > 0
            ? (balance / income) * 100
            : 0;

    const savingsRate = decimalValue(
        getMetricValue(
            summary,
            [
                "savings_rate",
                "saving_rate",
                "savingsRate",
            ],
            calculatedSavingsRate
        )
    );

    setText(
        "metric-income",
        formatCurrency(income)
    );

    setText(
        "metric-expense",
        formatCurrency(expense)
    );

    setText(
        "metric-balance",
        formatCurrency(balance)
    );

    setText(
        "metric-savings-rate",
        formatPercentage(savingsRate)
    );

    const metrics = getPayloadMetrics(payload);

    const needWant =
        getObjectValue(
            metrics,
            "need_want",
            {}
        );

    renderClassification(needWant);
}


function renderClassification(needWant) {
    const need = decimalValue(
        getMetricValue(
            needWant,
            [
                "need",
                "needs",
            ],
            0
        )
    );

    const want = decimalValue(
        getMetricValue(
            needWant,
            [
                "want",
                "wants",
            ],
            0
        )
    );

    const savings = decimalValue(
        getMetricValue(
            needWant,
            [
                "savings",
                "saving",
            ],
            0
        )
    );

    const total = need + want + savings;

    const needPercentage = decimalValue(
        getMetricValue(
            needWant,
            [
                "need_percentage",
                "needs_percentage",
                "needPercentage",
            ],
            total > 0
                ? (need / total) * 100
                : 0
        )
    );

    const wantPercentage = decimalValue(
        getMetricValue(
            needWant,
            [
                "want_percentage",
                "wants_percentage",
                "wantPercentage",
            ],
            total > 0
                ? (want / total) * 100
                : 0
        )
    );

    const savingsPercentage = decimalValue(
        getMetricValue(
            needWant,
            [
                "savings_percentage",
                "saving_percentage",
                "savingsPercentage",
            ],
            total > 0
                ? (savings / total) * 100
                : 0
        )
    );

    setText(
        "classification-need",
        formatCurrency(need)
    );

    setText(
        "classification-want",
        formatCurrency(want)
    );

    setText(
        "classification-saving",
        formatCurrency(savings)
    );

    setText(
        "classification-need-percent",
        formatPercentage(needPercentage)
    );

    setText(
        "classification-want-percent",
        formatPercentage(wantPercentage)
    );

    setText(
        "classification-saving-percent",
        formatPercentage(savingsPercentage)
    );

    const needBar = getElement(
        "classification-need-bar"
    );

    const wantBar = getElement(
        "classification-want-bar"
    );

    const savingBar = getElement(
        "classification-saving-bar"
    );

    if (
        !needBar
        || !wantBar
        || !savingBar
    ) {
        return;
    }

    if (total <= 0) {
        needBar.style.width = "0%";
        wantBar.style.width = "0%";
        savingBar.style.width = "0%";
        return;
    }

    needBar.style.width =
        ((need / total) * 100) + "%";

    wantBar.style.width =
        ((want / total) * 100) + "%";

    savingBar.style.width =
        ((savings / total) * 100) + "%";
}


function renderBehaviourSummaryBox(payload) {
    const container = getElement(
        "behaviour-summary-content"
    );

    if (!container) {
        return;
    }

    const metrics = getPayloadMetrics(payload);

    let behaviours = getObjectValue(
        metrics,
        "behaviours",
        null
    );

    if (!behaviours) {
        behaviours = getObjectValue(
            metrics,
            "behavior",
            {}
        );
    }

    const statistics = getObjectValue(
        behaviours,
        "statistics",
        {}
    );

    let concentration = getObjectValue(
        behaviours,
        "category_concentration",
        null
    );

    if (!concentration) {
        concentration = getObjectValue(
            behaviours,
            "categoryConcentration",
            {}
        );
    }

    const averageTransaction = decimalValue(
        getMetricValue(
            statistics,
            [
                "average_transaction",
                "averageTransaction",
            ],
            0
        )
    );

    const largestTransaction = decimalValue(
        getMetricValue(
            statistics,
            [
                "largest_transaction",
                "largestTransaction",
            ],
            0
        )
    );

    const transactionCount = getMetricValue(
        statistics,
        [
            "transaction_count",
            "transactionCount",
        ],
        0
    );

    const concentrationPercentage =
        decimalValue(
            getMetricValue(
                concentration,
                [
                    "concentration_percentage",
                    "concentrationPercentage",
                ],
                0
            )
        );

    const topCategory = getMetricValue(
        concentration,
        [
            "category",
            "top_category",
            "topCategory",
        ],
        "Not available"
    );

    container.innerHTML =
        '<div class="ai-summary-stat-row">'
        + '<span>Average transaction</span>'
        + '<strong>'
        + formatCurrency(averageTransaction)
        + '</strong>'
        + '</div>'

        + '<div class="ai-summary-stat-row">'
        + '<span>Largest transaction</span>'
        + '<strong>'
        + formatCurrency(largestTransaction)
        + '</strong>'
        + '</div>'

        + '<div class="ai-summary-stat-row">'
        + '<span>Expense transactions</span>'
        + '<strong>'
        + escapeHtml(transactionCount)
        + '</strong>'
        + '</div>'

        + '<div class="ai-summary-stat-row">'
        + '<span>Top category</span>'
        + '<strong>'
        + escapeHtml(topCategory)
        + '</strong>'
        + '</div>'

        + '<div class="ai-summary-stat-row">'
        + '<span>Category concentration</span>'
        + '<strong>'
        + formatPercentage(
            concentrationPercentage
        )
        + '</strong>'
        + '</div>';
}


function renderInsightSummaryBox(payload) {
    const container = getElement(
        "insight-summary-content"
    );

    if (!container) {
        return;
    }

    const insights = getPayloadInsights(
        payload
    );

    if (!insights.length) {
        container.innerHTML =
            '<p class="ai-summary-empty">'
            + 'No insights are available for this period.'
            + '</p>';

        return;
    }

    const mainInsight = insights[0];

    const insightType = getSafeInsightType(
        getObjectValue(
            mainInsight,
            "type",
            "neutral"
        )
    );

    const extraInsightCount =
        insights.length - 1;

    let additionalText = "";

    if (extraInsightCount > 0) {
        additionalText =
            '<small class="ai-summary-additional-count">'
            + escapeHtml(extraInsightCount)
            + ' additional signal'
            + (
                extraInsightCount === 1
                    ? ""
                    : "s"
            )
            + ' detected'
            + '</small>';
    }

    container.innerHTML =
        '<article class="ai-summary-highlight '
        + insightType
        + '">'
        + '<h3>'
        + escapeHtml(
            getObjectValue(
                mainInsight,
                "title",
                "Financial insight"
            )
        )
        + '</h3>'
        + '<p>'
        + escapeHtml(
            getObjectValue(
                mainInsight,
                "message",
                "No insight message is available."
            )
        )
        + '</p>'
        + additionalText
        + '</article>';
}


function renderPatternSummaryBox(payload) {
    const container = getElement(
        "pattern-summary-content"
    );

    if (!container) {
        return;
    }

    const metrics = getPayloadMetrics(payload);

    const comparison = getObjectValue(
        metrics,
        "comparison",
        {}
    );

    let behaviours = getObjectValue(
        metrics,
        "behaviours",
        null
    );

    if (!behaviours) {
        behaviours = getObjectValue(
            metrics,
            "behavior",
            {}
        );
    }

    let concentration = getObjectValue(
        behaviours,
        "category_concentration",
        null
    );

    if (!concentration) {
        concentration = getObjectValue(
            behaviours,
            "categoryConcentration",
            {}
        );
    }

    let largestExpenses = getObjectValue(
        behaviours,
        "largest_expenses",
        null
    );

    if (!largestExpenses) {
        largestExpenses = getObjectValue(
            behaviours,
            "largestExpenses",
            []
        );
    }

    largestExpenses = normalizeList(
        largestExpenses
    );

    const expenseChange = decimalValue(
        getMetricValue(
            comparison,
            [
                "expense_change_percentage",
                "expenseChangePercentage",
            ],
            0
        )
    );

    const concentrationPercentage =
        decimalValue(
            getMetricValue(
                concentration,
                [
                    "concentration_percentage",
                    "concentrationPercentage",
                ],
                0
            )
        );

    const topCategory = getMetricValue(
        concentration,
        [
            "category",
            "top_category",
            "topCategory",
        ],
        "one category"
    );

    const patterns = [];

    if (expenseChange >= 10) {
        patterns.push(
            {
                type: "warning",
                message:
                    "Expenses increased by "
                    + formatPercentage(
                        expenseChange
                    )
                    + " compared with the previous month.",
            }
        );
    } else if (expenseChange <= -10) {
        patterns.push(
            {
                type: "positive",
                message:
                    "Expenses decreased by "
                    + formatPercentage(
                        Math.abs(expenseChange)
                    )
                    + " compared with the previous month.",
            }
        );
    }

    if (concentrationPercentage >= 40) {
        patterns.push(
            {
                type: "neutral",
                message:
                    topCategory
                    + " represents "
                    + formatPercentage(
                        concentrationPercentage
                    )
                    + " of your classified expenses.",
            }
        );
    }

    if (largestExpenses.length) {
        const largest = largestExpenses[0];

        const largestAmount = getObjectValue(
            largest,
            "amount",
            0
        );

        const largestCategory = getObjectValue(
            largest,
            "category",
            "an uncategorized transaction"
        );

        patterns.push(
            {
                type: "neutral",
                message:
                    "Largest recorded expense: "
                    + formatCurrency(largestAmount)
                    + " for "
                    + largestCategory
                    + ".",
            }
        );
    }

    if (!patterns.length) {
        patterns.push(
            {
                type: "positive",
                message:
                    "No unusual spending pattern was detected "
                    + "for this period.",
            }
        );
    }

    container.innerHTML = patterns
        .slice(0, 3)
        .map(function (pattern) {
            const insightType = getSafeInsightType(
                pattern.type
            );

            return (
                '<div class="ai-summary-pattern-item '
                + insightType
                + '">'
                + '<i class="fa-solid fa-circle"></i>'
                + '<span>'
                + escapeHtml(pattern.message)
                + '</span>'
                + '</div>'
            );
        })
        .join("");
}


function renderBudgetSummaryBox(payload) {
    const container = getElement(
        "budget-summary-content"
    );

    if (!container) {
        return;
    }

    const metrics = getPayloadMetrics(payload);

    const budgetContainer = getObjectValue(
        metrics,
        "budgets",
        {}
    );

    let budgets = getObjectValue(
        budgetContainer,
        "budgets",
        null
    );

    if (!budgets) {
        budgets = normalizeList(
            budgetContainer
        );
    }

    budgets = normalizeList(budgets);

    const recommendations =
        getPayloadRecommendations(payload);

    let budgetHtml = "";

    if (budgets.length) {
        budgetHtml = budgets
            .slice(0, 2)
            .map(function (budget) {
                const details =
                    getBudgetStatusDetails(budget);

                const category = getMetricValue(
                    budget,
                    [
                        "category",
                    ],
                    "Overall budget"
                );

                const spent = formatCurrency(
                    getMetricValue(
                        budget,
                        [
                            "spent",
                        ],
                        0
                    )
                );

                const budgetLimit = formatCurrency(
                    getMetricValue(
                        budget,
                        [
                            "budget_limit",
                            "budgetLimit",
                        ],
                        0
                    )
                );

                return (
                    '<div class="ai-summary-budget-row">'
                    + '<div>'
                    + '<span>'
                    + escapeHtml(category)
                    + '</span>'
                    + '<small>'
                    + spent
                    + ' of '
                    + budgetLimit
                    + '</small>'
                    + '</div>'
                    + '<strong class="'
                    + details.cssClass
                    + '">'
                    + details.label
                    + '</strong>'
                    + '</div>'
                );
            })
            .join("");
    } else {
        budgetHtml =
            '<p class="ai-summary-empty">'
            + 'No active budgets for this period.'
            + '</p>';
    }

    let recommendationHtml = "";

    if (recommendations.length) {
        const recommendation =
            recommendations[0];

        const priority = getSafePriority(
            getObjectValue(
                recommendation,
                "priority",
                "medium"
            )
        );

        recommendationHtml =
            '<div class="ai-summary-recommendation '
            + priority
            + '">'
            + '<span class="ai-summary-recommendation-label">'
            + 'Suggested action'
            + '</span>'
            + '<strong>'
            + escapeHtml(
                getObjectValue(
                    recommendation,
                    "title",
                    "Continue tracking your finances"
                )
            )
            + '</strong>'
            + '<p>'
            + escapeHtml(
                getObjectValue(
                    recommendation,
                    "message",
                    "No recommendation message is available."
                )
            )
            + '</p>'
            + '</div>';
    } else {
        recommendationHtml =
            '<p class="ai-summary-empty">'
            + 'No recommendations are available.'
            + '</p>';
    }

    container.innerHTML =
        '<div class="ai-summary-budget-list">'
        + budgetHtml
        + '</div>'
        + recommendationHtml;
}


function renderFourSummaryBoxes(payload) {
    renderBehaviourSummaryBox(payload);

    renderInsightSummaryBox(payload);

    renderPatternSummaryBox(payload);

    renderBudgetSummaryBox(payload);
}


function renderForecast(data) {
    let dataset = getObjectValue(
        data,
        "dataset",
        null
    );

    if (!dataset) {
        dataset = getObjectValue(
            data,
            "data",
            []
        );
    }

    dataset = normalizeList(dataset);

    const confidenceElement = getElement(
        "forecast-confidence"
    );

    const valueElement = getElement(
        "forecast-value"
    );

    if (!dataset.length) {
        if (confidenceElement) {
            confidenceElement.textContent =
                "Not enough history for a baseline.";
        }

        if (valueElement) {
            valueElement.textContent =
                formatCurrency(0);
        }

        return;
    }

    const values = dataset.map(
        function (item) {
            return decimalValue(
                getMetricValue(
                    item,
                    [
                        "expense",
                        "expenses",
                        "value",
                    ],
                    0
                )
            );
        }
    );

    const average = values.reduce(
        function (total, value) {
            return total + value;
        },
        0
    ) / values.length;

    if (valueElement) {
        valueElement.textContent =
            formatCurrency(average);
    }

    if (confidenceElement) {
        confidenceElement.textContent =
            String(dataset.length)
            + " months of history used";
    }
}


function setButtonLoading(isLoading) {
    const button = getElement(
        "generate-summary"
    );

    if (!button) {
        return;
    }

    button.disabled = isLoading;

    if (isLoading) {
        button.innerHTML =
            '<i class="fa-solid fa-spinner fa-spin"></i>'
            + " Generating...";
    } else {
        button.innerHTML =
            '<i class="fa-solid fa-arrows-rotate"></i>'
            + " Generate summary";
    }
}


async function loadSummary() {
    hideError();

    setButtonLoading(true);

    try {
        const summaryPayload =
            await fetchSummary();

        renderSummaryText(summaryPayload);

        renderMetrics(summaryPayload);

        renderFourSummaryBoxes(summaryPayload);

        let forecastPayload = {};

        try {
            forecastPayload =
                await fetchForecastData();
        } catch (error) {
            forecastPayload = {};
        }

        renderForecast(forecastPayload);

        setText(
            "summary-updated",
            "Updated "
            + new Date().toLocaleTimeString(
                "en-IN",
                {
                    hour: "2-digit",
                    minute: "2-digit",
                }
            )
        );
    } catch (error) {
        const message = error && error.message
            ? error.message
            : "Unable to generate summary.";

        showError(message);
    } finally {
        setButtonLoading(false);
    }
}


function bindEvents() {
    const button = getElement(
        "generate-summary"
    );

    if (button) {
        button.addEventListener(
            "click",
            loadSummary
        );
    }
}


document.addEventListener(
    "DOMContentLoaded",
    function () {
        populateYears();

        initializePeriod();

        renderInitialMetrics();

        bindEvents();

        loadSummary();
    }
);