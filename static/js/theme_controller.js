/**
 * CPD ANALYTICS CORE // THEME CONTROLLER (MODO DÍA / MODO NOCHE)
 * Persistencia en localStorage y sincronización reactiva en tiempo real.
 */

(function () {
    const THEME_STORAGE_KEY = 'cpd_theme';

    function getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function getCurrentTheme() {
        return localStorage.getItem(THEME_STORAGE_KEY) || getSystemTheme();
    }

    function applyTheme(theme) {
        const root = document.documentElement;
        if (theme === 'dark') {
            root.classList.add('dark');
            root.classList.remove('light');
        } else {
            root.classList.add('light');
            root.classList.remove('dark');
        }

        // Actualizar iconos de todos los botones de tema en la interfaz
        updateThemeToggleIcons(theme);

        // Notificar a componentes interesados (ej. mapas o gráficos)
        window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    }

    function updateThemeToggleIcons(theme) {
        const toggleButtons = document.querySelectorAll('[data-theme-toggle]');
        toggleButtons.forEach(btn => {
            const icon = btn.querySelector('.theme-icon');
            const label = btn.querySelector('.theme-label');
            if (theme === 'dark') {
                if (icon) icon.textContent = 'light_mode';
                if (label) label.textContent = 'Modo Día';
                btn.setAttribute('title', 'Cambiar a Modo Día');
            } else {
                if (icon) icon.textContent = 'dark_mode';
                if (label) label.textContent = 'Modo Noche';
                btn.setAttribute('title', 'Cambiar a Modo Noche');
            }
        });
    }

    function toggleTheme() {
        const current = getCurrentTheme();
        const nextTheme = current === 'dark' ? 'light' : 'dark';
        localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
        applyTheme(nextTheme);
    }

    // Inicializar listeners al cargar el DOM
    document.addEventListener('DOMContentLoaded', () => {
        applyTheme(getCurrentTheme());

        document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                toggleTheme();
            });
        });

        // Escuchar cambios del sistema operativo
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem(THEME_STORAGE_KEY)) {
                applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    });

    // Exponer función de toggle global
    window.toggleCPDTheme = toggleTheme;
})();
