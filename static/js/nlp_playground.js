/**
 * CPD ANALYTICS CORE // INFERENCE PLAYGROUND NLP
 * Clasificador semántico interactivo de reportes policiales con AJAX a Flask API.
 */

const EXAMPLES = {
    1: "RETAIL THEFT AT TARGET DEPARTMENT STORE. INDIVIDUAL CONCEALED COSMETICS AND ELECTRONIC ACCESSORIES IN BACKPACK, PASSED ALL CASH REGISTERS WITHOUT PAYMENT.",
    2: "ARMED ROBBERY AT GAS STATION CONVENIENCE STORE. TWO SUSPECTS WITH HANDGUN DISPLAYED, DEMANDED CASH DRAWER, FLED ON FOOT SOUTHBOUND.",
    3: "DOMESTIC BATTERY REPORTED AT MULTI-UNIT APARTMENT RESIDENCE. VERBAL ARGUMENT BETWEEN SPOUSES ESCALATED INTO PHYSICAL ALTERCATION WITH MINOR INJURIES.",
    4: "CRIMINAL DAMAGE TO VEHICLE ON PUBLIC STREET OVERNIGHT. CATALYTIC CONVERTER SAWED OFF PARKED HONDA CRV, DRIVER SIDE WINDOW SMASHED."
};

function loadExample(id) {
    const textarea = document.getElementById('incident-input');
    const counter = document.getElementById('char-counter');
    if (textarea && EXAMPLES[id]) {
        textarea.value = EXAMPLES[id];
        if (counter) counter.textContent = `${textarea.value.length} caracteres`;
        analyzeIncidentText(textarea.value);
    }
}

function clearIncidentInput() {
    const textarea = document.getElementById('incident-input');
    const counter = document.getElementById('char-counter');
    if (textarea) {
        textarea.value = '';
        if (counter) counter.textContent = '0 caracteres';
        textarea.focus();
    }
}

async function analyzeIncidentText(text) {
    if (!text || text.trim().length === 0) return;

    const analyzeBtn = document.getElementById('btn-analyze-text');
    const btnText = document.getElementById('analyze-btn-text');
    if (analyzeBtn) {
        analyzeBtn.disabled = true;
        if (btnText) btnText.textContent = "PROCESANDO INFERENCIA...";
    }

    try {
        const response = await fetch('/api/v1/predict_nlp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });

        const data = await response.json();
        if (data.success) {
            updateNLPResultsUI(data);
        }
    } catch (err) {
        console.error("Error en inferencia NLP:", err);
    } finally {
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
            if (btnText) btnText.textContent = "EJECUTAR INFERENCIA NLP";
        }
    }
}

function updateNLPResultsUI(data) {
    // 1. Título y Código del Cluster
    const titleEl = document.getElementById('res-cluster-title');
    const codeEl = document.getElementById('res-cluster-code');
    const descEl = document.getElementById('res-cluster-desc');
    const locEl = document.getElementById('res-location-focus');
    const hoursEl = document.getElementById('res-peak-hours');
    const arrestEl = document.getElementById('res-arrest-prob');
    const confValEl = document.getElementById('res-confidence-val');
    const confBarEl = document.getElementById('res-confidence-bar');
    const keywordsContainer = document.getElementById('res-keywords-container');

    if (titleEl) titleEl.textContent = data.cluster_title;
    if (codeEl) codeEl.textContent = data.cluster_code;
    if (descEl) descEl.textContent = data.description;
    if (locEl) locEl.textContent = data.location_focus;
    if (hoursEl) hoursEl.textContent = data.peak_hours;
    if (arrestEl) arrestEl.textContent = data.arrest_prob;

    if (confValEl) confValEl.textContent = `${data.confidence}%`;
    if (confBarEl) confBarEl.style.width = `${data.confidence}%`;

    // 2. Palabras clave TF-IDF activas
    if (keywordsContainer && data.matched_keywords) {
        keywordsContainer.innerHTML = '';
        data.matched_keywords.forEach(kw => {
            const badge = document.createElement('span');
            badge.className = "px-2 py-0.5 rounded bg-surface-container-high border border-outline-variant/60 text-primary-container font-data-code text-xs font-semibold uppercase tracking-wider flex items-center gap-1 shadow-sm";
            badge.innerHTML = `<span class="size-1.5 rounded-full bg-primary-container"></span>${kw}`;
            keywordsContainer.appendChild(badge);
        });
    }

    // 3. Indicador LSA 2D
    const lsaTarget = document.getElementById('lsa-pointer-dot');
    if (lsaTarget && data.lsa_coords) {
        // Mapear [-1, 1] a [10%, 90%] del SVG/Canvas
        const xPercent = 50 + (data.lsa_coords.x * 38);
        const yPercent = 50 - (data.lsa_coords.y * 38);
        lsaTarget.style.left = `${xPercent}%`;
        lsaTarget.style.top = `${yPercent}%`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const textarea = document.getElementById('incident-input');
    const counter = document.getElementById('char-counter');
    const analyzeBtn = document.getElementById('btn-analyze-text');
    const clearBtn = document.getElementById('btn-clear-input');

    if (textarea && counter) {
        textarea.addEventListener('input', () => {
            counter.textContent = `${textarea.value.length} caracteres`;
        });
    }

    if (analyzeBtn && textarea) {
        analyzeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            analyzeIncidentText(textarea.value);
        });
    }

    if (clearBtn) {
        clearBtn.addEventListener('click', (e) => {
            e.preventDefault();
            clearIncidentInput();
        });
    }
});
