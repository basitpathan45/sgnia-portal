// Apply the saved or system color theme before the page styles render.
const themePreferenceKey = "sgnia-theme";
const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");

function readThemePreference() {
  try {
    return localStorage.getItem(themePreferenceKey);
  } catch (error) {
    console.warn("The saved theme preference could not be read.", error);
    return null;
  }
}

function applyTheme(theme) {
  const isDark = theme === "dark";
  document.documentElement.dataset.theme = isDark ? "dark" : "light";

  const toggle = document.querySelector("#theme-toggle");
  if (toggle) {
    toggle.setAttribute("aria-pressed", String(isDark));
    toggle.setAttribute("aria-label", `Switch to ${isDark ? "light" : "dark"} theme`);
    toggle.querySelector(".theme-toggle-icon").textContent = isDark ? "☀" : "☾";
    toggle.querySelector(".theme-toggle-label").textContent = isDark ? "Day mode" : "Night mode";
  }
}

function storeThemePreference(theme) {
  try {
    localStorage.setItem(themePreferenceKey, theme);
  } catch (error) {
    console.warn("The theme preference could not be saved.", error);
  }
}

const savedTheme = readThemePreference();
applyTheme(savedTheme || (systemTheme.matches ? "dark" : "light"));

document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.querySelector("#theme-toggle");
  if (!toggle) return;

  applyTheme(document.documentElement.dataset.theme);
  toggle.addEventListener("click", () => {
    const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(nextTheme);
    storeThemePreference(nextTheme);
  });

  systemTheme.addEventListener("change", (event) => {
    if (!readThemePreference()) applyTheme(event.matches ? "dark" : "light");
  });
});
