document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");
    const mobileMenuButton = document.getElementById("mobileMenuButton");
    const mobileOverlay = document.getElementById("mobileOverlay");
    const themeToggle = document.getElementById("themeToggle");

    const desktopMediaQuery = window.matchMedia("(min-width: 769px)");

    /* Sidebar desktop state */

    function applySidebarState() {
        if (!desktopMediaQuery.matches) {
            document.body.classList.remove("sidebar-collapsed");
            return;
        }

        const savedState = localStorage.getItem(
            "expenseTrackerSidebar"
        );

        if (savedState === "expanded") {
            document.body.classList.remove("sidebar-collapsed");
        } else {
            document.body.classList.add("sidebar-collapsed");
        }
    }

    applySidebarState();

    sidebarToggle?.addEventListener("click", () => {
        if (!desktopMediaQuery.matches) {
            return;
        }

        document.body.classList.toggle("sidebar-collapsed");

        const isCollapsed = document.body.classList.contains(
            "sidebar-collapsed"
        );

        localStorage.setItem(
            "expenseTrackerSidebar",
            isCollapsed ? "collapsed" : "expanded"
        );
    });

    desktopMediaQuery.addEventListener("change", () => {
        applySidebarState();
        closeMobileSidebar();
    });

    /* Mobile sidebar */

    function closeMobileSidebar() {
        sidebar?.classList.remove("mobile-open");
        mobileOverlay?.classList.remove("visible");
        document.body.classList.remove("sidebar-is-open");
    }

    mobileMenuButton?.addEventListener("click", () => {
        sidebar?.classList.add("mobile-open");
        mobileOverlay?.classList.add("visible");
        document.body.classList.add("sidebar-is-open");
    });

    mobileOverlay?.addEventListener(
        "click",
        closeMobileSidebar
    );

    sidebar?.querySelectorAll(".nav-link").forEach((link) => {
        link.addEventListener("click", closeMobileSidebar);
    });

    /* Theme */

    const savedTheme = localStorage.getItem(
        "expenseTrackerTheme"
    );

    const currentTheme = savedTheme || "light";

    document.documentElement.dataset.theme = currentTheme;
    updateThemeIcon(currentTheme);

    themeToggle?.addEventListener("click", () => {
        const activeTheme =
            document.documentElement.dataset.theme || "light";

        const nextTheme =
            activeTheme === "light" ? "dark" : "light";

        document.documentElement.dataset.theme = nextTheme;

        localStorage.setItem(
            "expenseTrackerTheme",
            nextTheme
        );

        updateThemeIcon(nextTheme);
    });

    function updateThemeIcon(theme) {
        const icon = themeToggle?.querySelector("i");

        if (!icon) {
            return;
        }

        icon.className =
            theme === "dark"
                ? "fa-regular fa-sun"
                : "fa-regular fa-moon";
    }

    /* Monthly expense chart */

    const trendElement = document.getElementById(
        "monthly-trend-data"
    );

    const chartCanvas = document.getElementById(
        "monthlyExpenseChart"
    );

    if (
        !trendElement ||
        !chartCanvas ||
        typeof Chart === "undefined"
    ) {
        return;
    }

    let trendData = [];

    try {
        trendData = JSON.parse(
            trendElement.textContent
        );
    } catch (error) {
        console.error(
            "Unable to parse monthly trend data.",
            error
        );

        return;
    }

    if (!Array.isArray(trendData)) {
        return;
    }

    const labels = trendData.map((item) => {
        return item.month || item.label || "";
    });

    const values = trendData.map((item) => {
        return Number(
            item.expense ??
            item.amount ??
            item.value ??
            0
        );
    });

    const styles = getComputedStyle(
        document.documentElement
    );

    const accentColor = styles
        .getPropertyValue("--accent")
        .trim();

    const mutedColor = styles
        .getPropertyValue("--text-soft")
        .trim();

    new Chart(chartCanvas, {
        type: "bar",

        data: {
            labels,
            datasets: [
                {
                    label: "Expenses",
                    data: values,
                    backgroundColor: accentColor,
                    borderRadius: 6,
                    borderSkipped: false,
                    maxBarThickness: 32,
                },
            ],
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            plugins: {
                legend: {
                    display: false,
                },

                tooltip: {
                    callbacks: {
                        label: (context) => {
                            return ` ₹${Number(
                                context.raw
                            ).toLocaleString("en-IN")}`;
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
                        color: mutedColor,
                        font: {
                            family: "Manrope",
                            size: 10,
                        },
                    },
                },

                y: {
                    beginAtZero: true,

                    grid: {
                        color:
                            "rgba(136, 125, 112, 0.14)",
                    },

                    ticks: {
                        color: mutedColor,
                        font: {
                            family: "Manrope",
                            size: 10,
                        },

                        callback: (value) => {
                            return `₹${Number(
                                value
                            ).toLocaleString("en-IN")}`;
                        },
                    },
                },
            },
        },
    });
});