// Search
const searchInput = document.getElementById("searchInput");
if (searchInput) {
    searchInput.addEventListener("keyup", function () {
        const filter = this.value.toUpperCase();
        const rows = document.querySelector("#leaderboardTable tbody").rows;
        for (const row of rows) {
            const cityCell = row.querySelector(".city-name");
            if (!cityCell) continue;
            row.style.display = cityCell.textContent.toUpperCase().includes(filter)
                ? ""
                : "none";
        }
    });
}

// Theme Switcher
const themeIcons = {
    light: "☀️",
    dark: "🌙",
    glacier: "🧊"
};

// Get saved theme, otherwise use system preference
let currentTheme = localStorage.getItem("theme");

if (!currentTheme) {
    currentTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
}

// Apply theme immediately
document.documentElement.setAttribute("data-bs-theme", currentTheme);

// Update navbar icon
const activeThemeIcon = document.getElementById("theme-icon-active");

function updateThemeIcon(theme) {
    if (activeThemeIcon) {
        activeThemeIcon.textContent = themeIcons[theme] || "🌓";
    }
}

updateThemeIcon(currentTheme);

// Theme buttons
document.querySelectorAll("[data-bs-theme-value]").forEach(button => {
    button.addEventListener("click", () => {
        const theme = button.dataset.bsThemeValue;

        localStorage.setItem("theme", theme);
        document.documentElement.setAttribute("data-bs-theme", theme);

        updateThemeIcon(theme);
    });
});
