/**
 * CPD ANALYTICS CORE // RESPONSIVE DRAWER & NAVIGATION
 * Manejo accesible del menú lateral off-canvas para Smartphone y Tabletas.
 */

(function () {
    document.addEventListener('DOMContentLoaded', () => {
        const drawerBackdrop = document.getElementById('mobile-drawer-backdrop');
        const drawerPanel = document.getElementById('mobile-drawer-panel');
        const openBtn = document.getElementById('btn-mobile-drawer-open');
        const closeBtn = document.getElementById('btn-mobile-drawer-close');

        function openDrawer() {
            if (drawerBackdrop && drawerPanel) {
                drawerBackdrop.classList.add('active');
                drawerPanel.classList.add('active');
                document.body.classList.add('overflow-hidden');
            }
        }

        function closeDrawer() {
            if (drawerBackdrop && drawerPanel) {
                drawerBackdrop.classList.remove('active');
                drawerPanel.classList.remove('active');
                document.body.classList.remove('overflow-hidden');
            }
        }

        if (openBtn) {
            openBtn.addEventListener('click', (e) => {
                e.preventDefault();
                openDrawer();
            });
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                closeDrawer();
            });
        }

        if (drawerBackdrop) {
            drawerBackdrop.addEventListener('click', (e) => {
                if (e.target === drawerBackdrop) {
                    closeDrawer();
                }
            });
        }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeDrawer();
            }
        });
    });
})();
