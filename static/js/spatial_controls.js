/**
 * CPD ANALYTICS CORE // SPATIAL & DENSITY CONTROLS
 * Control de sliders Haversine, conmutador de capas y HUD adaptativo para móvil/desktop.
 */

document.addEventListener('DOMContentLoaded', () => {
    const epsSlider = document.getElementById('slider-eps');
    const minPtsSlider = document.getElementById('slider-min-pts');
    const epsValDisplay = document.getElementById('val-eps-display');
    const minPtsValDisplay = document.getElementById('val-min-pts-display');
    const hotspotsCountDisplay = document.getElementById('val-hotspots-count');
    const noiseCountDisplay = document.getElementById('val-noise-count');

    // Bottom sheet controls en móvil
    const mobileHudToggle = document.getElementById('btn-mobile-hud-toggle');
    const mobileHudClose = document.getElementById('btn-mobile-hud-close');
    const hudContainer = document.getElementById('spatial-hud-box');

    if (mobileHudToggle && hudContainer) {
        mobileHudToggle.addEventListener('click', () => {
            hudContainer.classList.toggle('hidden');
            hudContainer.classList.toggle('active');
        });
    }

    if (mobileHudClose && hudContainer) {
        mobileHudClose.addEventListener('click', () => {
            hudContainer.classList.add('hidden');
            hudContainer.classList.remove('active');
        });
    }

    async function updateSpatialParams() {
        const eps = epsSlider ? parseInt(epsSlider.value) : 300;
        const minPts = minPtsSlider ? parseInt(minPtsSlider.value) : 25;

        if (epsValDisplay) {
            const epsRad = (eps / 6371008.8).toFixed(6);
            epsValDisplay.textContent = `${eps} m (${epsRad} rad)`;
        }

        if (minPtsValDisplay) {
            minPtsValDisplay.textContent = `${minPts} pts`;
        }

        try {
            const res = await fetch(`/api/v1/spatial_filter?eps=${eps}&min_pts=${minPts}`);
            const data = await res.json();
            if (data.active_hotspots && hotspotsCountDisplay) {
                hotspotsCountDisplay.textContent = `${data.active_hotspots} ZONAS`;
            }
            if (data.noise_count && noiseCountDisplay) {
                noiseCountDisplay.textContent = `Ruido (-1): ${data.noise_count} pts (${data.noise_pct}%)`;
            }
        } catch (e) {
            console.error("Error al actualizar parámetros espaciales:", e);
        }
    }

    if (epsSlider) {
        epsSlider.addEventListener('input', updateSpatialParams);
    }
    if (minPtsSlider) {
        minPtsSlider.addEventListener('input', updateSpatialParams);
    }

    // Layer checkboxes
    const layerButtons = document.querySelectorAll('[data-layer-toggle]');
    layerButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const icon = btn.querySelector('.material-symbols-outlined');
            const isActive = btn.classList.contains('active-layer');
            if (isActive) {
                btn.classList.remove('active-layer', 'bg-primary-container', 'text-on-primary', 'font-bold');
                btn.classList.add('bg-surface-container', 'text-on-surface-variant');
                if (icon) icon.textContent = 'check_box_outline_blank';
            } else {
                btn.classList.add('active-layer', 'bg-primary-container', 'text-on-primary', 'font-bold');
                btn.classList.remove('bg-surface-container', 'text-on-surface-variant');
                if (icon) icon.textContent = 'check_box';
            }
        });
    });
});
