/**
 * GLOBO 3D WEBGIS // PLATAFORMA DE INTELIGENCIA URBANA
 * MapLibre GL JS v4+ con soporte Dual Dinámico (Bolivia ↔ Chicago), Clustering WebGL y Teselas Vectoriales
 * Directriz de Diseño: Cero emojis, High Data-Ink Ratio, micro-badges tácticos
 */

document.addEventListener('DOMContentLoaded', () => {
    let map;
    let isGlobeProjection = true;
    let currentGeojson = null;

    // Detectar contexto activo inicial desde URL (?ctx=chicago o ?ctx=bolivia) o atributo DOM
    const viewportEl = document.getElementById('globo-viewport');
    const urlParams = new URLSearchParams(window.location.search);
    let activeContext = (urlParams.get('ctx') || (viewportEl ? viewportEl.dataset.context : 'bolivia') || 'bolivia').toLowerCase();

    // Elementos del DOM
    const statTotalEl = document.getElementById('stat-total-events');
    const filterCategoryEl = document.getElementById('filter-category');
    const filterCityEl = document.getElementById('filter-city');
    const btnToggleProj = document.getElementById('btn-toggle-projection');
    const btnToggleCluster = document.getElementById('btn-toggle-cluster');
    const bottomControlsEl = document.querySelector('.hud-bottom-controls');
    const btnSwitchBolivia = document.getElementById('btn-switch-bolivia');
    const btnSwitchChicago = document.getElementById('btn-switch-chicago');

    let isClusteringEnabled = true;

    // Selectores del Modo Algorítmico (Delito / DBSCAN / HDBSCAN / OPTICS / GMM / Ward)
    const btnModeCategory = document.getElementById('btn-mode-category');
    const btnModeDbscan = document.getElementById('btn-mode-dbscan');
    const btnModeHdbscan = document.getElementById('btn-mode-hdbscan');
    const btnModeOptics = document.getElementById('btn-mode-optics');
    const btnModeGmm = document.getElementById('btn-mode-gmm');
    const btnModeWard = document.getElementById('btn-mode-ward');
    const activeModeLabel = document.getElementById('active-mode-label');

    // Secciones de Leyenda
    const legendCategory = document.getElementById('legend-category-section');
    const legendDbscan = document.getElementById('legend-dbscan-section');
    const legendHdbscan = document.getElementById('legend-hdbscan-section');
    const legendOptics = document.getElementById('legend-optics-section');
    const legendGmm = document.getElementById('legend-gmm-section');
    const legendWard = document.getElementById('legend-ward-section');

    let currentClusterMode = 'category';

    // Modelado Gaussiano Multivariante (GMM): Parámetros de Covarianza y Elipses 2-sigma
    const GMM_COMPONENTS_DATA = {
        bolivia: [
            {
                id: 0,
                label: "GMM #0 (π=0.14)",
                name: "Plan 3000 / Los Lotes",
                center: [-63.1529, -17.8356],
                a: 3436,
                b: 1200,
                angle: -148.1,
                color: "#ff3366",
                weight: 0.14,
                description: "Cuenca urbana periférica de alta tasa de agresión física y robo agravado (Plan 3000 / Los Lotes)."
            },
            {
                id: 1,
                label: "GMM #1 (π=0.24)",
                name: "La Paz Centro & Prado",
                center: [-68.1350, -16.4972],
                a: 1886,
                b: 1200,
                angle: 142.7,
                color: "#818cf8",
                weight: 0.24,
                description: "Corredor andino de alta concentración topográfica (El Prado / Centro Paceño)."
            },
            {
                id: 2,
                label: "GMM #2 (π=0.18)",
                name: "Cochabamba Cercado",
                center: [-66.1570, -17.3935],
                a: 1800,
                b: 1200,
                angle: 90.0,
                color: "#34d399",
                weight: 0.18,
                description: "Eje metropolitano de delitos patrimoniales y lesiones en Cercado y Cancha."
            },
            {
                id: 3,
                label: "GMM #3 (π=0.45)",
                name: "SCZ Casco & Equipetrol",
                center: [-63.1789, -17.7797],
                a: 3899,
                b: 1561,
                angle: -168.8,
                color: "#00e5ff",
                weight: 0.45,
                description: "Núcleo de alta densidad transaccional y delitos patrimoniales (SCZ Casco & Equipetrol)."
            }
        ],
        chicago: [
            {
                id: 0,
                label: "GMM #0 (π=0.22)",
                name: "The Loop / Central West",
                center: [-87.6672, 41.8816],
                a: 8534,
                b: 2849,
                angle: -170.1,
                color: "#00e5ff",
                weight: 0.22,
                description: "Alta densidad de hurtos diurnos (Theft) y delitos patrimoniales comerciales."
            },
            {
                id: 1,
                label: "GMM #1 (π=0.45)",
                name: "South Side (Englewood/Gresham)",
                center: [-87.6317, 41.7581],
                a: 10746,
                b: 6282,
                angle: 122.4,
                color: "#ff3366",
                weight: 0.45,
                description: "Corredor sur con concentración de delitos violentos y asaltos armados (Distritos 6, 7)."
            },
            {
                id: 2,
                label: "GMM #2 (π=0.32)",
                name: "West & North Side (Garfield/Austin)",
                center: [-87.7142, 41.9321],
                a: 11620,
                b: 6012,
                angle: -136.6,
                color: "#ffaa00",
                weight: 0.32,
                description: "Foco crítico de agresiones (Battery), robos y armas (Distritos 11, 15, 25)."
            }
        ]
    };

    // Función Geodésica: Construye un Polígono regular de 64 vértices rotado según matriz de covarianza
    function createEllipsePolygon(centerLng, centerLat, a, b, angleDeg, steps = 64) {
        const coordinates = [];
        const angleRad = (angleDeg * Math.PI) / 180;
        const cosA = Math.cos(angleRad);
        const sinA = Math.sin(angleRad);
        const latRad = (centerLat * Math.PI) / 180;
        const metersPerDegreeLat = 111320;
        const metersPerDegreeLng = 111320 * Math.cos(latRad);

        for (let i = 0; i <= steps; i++) {
            const theta = (i * 2 * Math.PI) / steps;
            const ex = a * Math.cos(theta);
            const ey = b * Math.sin(theta);
            const xRot = ex * cosA - ey * sinA;
            const yRot = ex * sinA + ey * cosA;
            const lng = centerLng + (xRot / metersPerDegreeLng);
            const lat = centerLat + (yRot / metersPerDegreeLat);
            coordinates.push([lng, lat]);
        }
        if (coordinates.length > 0) {
            coordinates[coordinates.length - 1] = coordinates[0];
        }
        return [coordinates];
    }

    // Genera GeoJSON de Elipses 2-sigma (86.5% de la masa probabilística de la Gaussiana)
    function generateGmmEllipsesGeojson(ctx) {
        const components = GMM_COMPONENTS_DATA[ctx] || GMM_COMPONENTS_DATA['bolivia'];
        const features = components.map(comp => ({
            type: 'Feature',
            geometry: {
                type: 'Polygon',
                coordinates: createEllipsePolygon(comp.center[0], comp.center[1], comp.a, comp.b, comp.angle, 64)
            },
            properties: {
                id: comp.id,
                name: comp.name,
                label: comp.label,
                color: comp.color,
                weight: comp.weight,
                weight_percent: Math.round(comp.weight * 100),
                a: comp.a,
                b: comp.b,
                angle: comp.angle,
                center_lng: comp.center[0],
                center_lat: comp.center[1],
                description: comp.description
            }
        }));

        return {
            type: 'FeatureCollection',
            features: features
        };
    }

    // Genera GeoJSON de Centroides y Etiquetas de Ponderación (π)
    function generateGmmCentroidsGeojson(ctx) {
        const components = GMM_COMPONENTS_DATA[ctx] || GMM_COMPONENTS_DATA['bolivia'];
        const features = components.map(comp => ({
            type: 'Feature',
            geometry: {
                type: 'Point',
                coordinates: [comp.center[0], comp.center[1]]
            },
            properties: {
                id: comp.id,
                name: comp.name,
                label: comp.label,
                color: comp.color,
                weight: comp.weight,
                weight_percent: Math.round(comp.weight * 100),
                a: comp.a,
                b: comp.b,
                angle: comp.angle,
                center_lng: comp.center[0],
                center_lat: comp.center[1],
                description: comp.description
            }
        }));

        return {
            type: 'FeatureCollection',
            features: features
        };
    }

    // Actualiza el contenido de las leyendas dinámicamente según el contexto (Bolivia ↔ Chicago)
    function updateLegends(ctx) {
        if (ctx === 'chicago') {
            if (legendDbscan) {
                legendDbscan.innerHTML = `
                    <span class="text-[10px] text-cyan-400 uppercase tracking-wider block font-bold mb-1">DBSCAN Hotspots</span>
                    <div class="legend-item"><span class="legend-dot bg-[#00e5ff]"></span><span class="text-on-surface text-[11px]">#1 The Loop</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#ff3366]"></span><span class="text-on-surface text-[11px]">#2 Harrison West</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#ffaa00]"></span><span class="text-on-surface text-[11px]">#3 Englewood South</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#a855f7]"></span><span class="text-on-surface text-[11px]">#4 Near West UIC</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#64748b]"></span><span class="text-outline text-[11px]">Ruido Espacial (-1)</span></div>
                `;
            }
            if (legendHdbscan) {
                legendHdbscan.innerHTML = `
                    <span class="text-[10px] text-teal-400 uppercase tracking-wider block font-bold mb-1">HDBSCAN Persistencia</span>
                    <div class="legend-item"><span class="legend-dot bg-[#00e5ff]"></span><span class="text-on-surface text-[11px]">#1 Loop Core (&lambda;=0.92)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#ff3366]"></span><span class="text-on-surface text-[11px]">#2 West Side (&lambda;=0.88)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#ffaa00]"></span><span class="text-on-surface text-[11px]">#3 Englewood (&lambda;=0.81)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#a855f7]"></span><span class="text-on-surface text-[11px]">#4 Near West (&lambda;=0.71)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#64748b]"></span><span class="text-outline text-[11px]">Ruido Multiescala (-1)</span></div>
                `;
            }
            if (legendOptics) {
                legendOptics.innerHTML = `
                    <span class="text-[10px] text-amber-400 uppercase tracking-wider block font-bold mb-1">OPTICS Valles (&xi;)</span>
                    <div class="legend-item"><span class="legend-dot bg-[#00e5ff]"></span><span class="text-on-surface text-[11px]">Valle #1 Loop (88m)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#ff3366]"></span><span class="text-on-surface text-[11px]">Valle #2 Harrison (125m)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#ffaa00]"></span><span class="text-on-surface text-[11px]">Valle #3 Englewood (145m)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#a855f7]"></span><span class="text-on-surface text-[11px]">Valle #4 Near West (172m)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#64748b]"></span><span class="text-outline text-[11px]">Pico Ruido / Salto</span></div>
                `;
            }
            if (legendGmm) {
                legendGmm.innerHTML = `
                    <span class="text-[10px] text-emerald-400 uppercase tracking-wider block font-bold mb-1">GMM Gaussianas (&pi;)</span>
                    <div class="legend-item"><span class="legend-dot bg-[#00e5ff]"></span><span class="text-on-surface text-[11px]">Loop Comercial (&pi;=0.35)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#ff3366]"></span><span class="text-on-surface text-[11px]">West Side (&pi;=0.40)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#ffaa00]"></span><span class="text-on-surface text-[11px]">South Side (&pi;=0.25)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#64748b]"></span><span class="text-outline text-[11px]">Dispersión (>3&sigma;)</span></div>
                `;
            }
            if (legendWard) {
                legendWard.innerHTML = `
                    <span class="text-[10px] text-purple-400 uppercase tracking-wider block font-bold mb-1">Ward Macro-Clusters</span>
                    <div class="legend-item"><span class="legend-dot bg-[#ff3366]"></span><span class="text-on-surface text-[11px]">Macro A: West/South Side</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#00e5ff]"></span><span class="text-on-surface text-[11px]">Macro B: Loop Comercial</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#34d399]"></span><span class="text-on-surface text-[11px]">Macro C: Residencial</span></div>
                `;
            }
        } else {
            if (legendDbscan) {
                legendDbscan.innerHTML = `
                    <span class="text-[10px] text-cyan-400 uppercase tracking-wider block font-bold mb-1">DBSCAN Hotspots</span>
                    <div class="legend-item"><span class="legend-dot bg-[#00e5ff]"></span><span class="text-on-surface text-[11px]">#0 Santa Cruz Core</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#34d399]"></span><span class="text-on-surface text-[11px]">#1 Cochabamba</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#ff3366]"></span><span class="text-on-surface text-[11px]">#2 Plan 3000 / Lotes</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#818cf8]"></span><span class="text-on-surface text-[11px]">#5 La Paz Centro</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#64748b]"></span><span class="text-outline text-[11px]">Ruido Espacial (-1)</span></div>
                `;
            }
            if (legendHdbscan) {
                legendHdbscan.innerHTML = `
                    <span class="text-[10px] text-teal-400 uppercase tracking-wider block font-bold mb-1">HDBSCAN Persistencia</span>
                    <div class="legend-item"><span class="legend-dot bg-[#00e5ff]"></span><span class="text-on-surface text-[11px]">#5 SCZ Metrop. (&lambda;=0.89)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#818cf8]"></span><span class="text-on-surface text-[11px]">#10 La Paz Centro (&lambda;=0.84)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#34d399]"></span><span class="text-on-surface text-[11px]">#0 CBBA Valle (&lambda;=0.78)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#ff3366]"></span><span class="text-on-surface text-[11px]">#1 Plan 3000 (&lambda;=0.75)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#fbbf24]"></span><span class="text-on-surface text-[11px]">#4 SCZ Periferia (&lambda;=0.62)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#64748b]"></span><span class="text-outline text-[11px]">Ruido Multiescala (-1)</span></div>
                `;
            }
            if (legendOptics) {
                legendOptics.innerHTML = `
                    <span class="text-[10px] text-amber-400 uppercase tracking-wider block font-bold mb-1">OPTICS Valles (&xi;)</span>
                    <div class="legend-item"><span class="legend-dot bg-[#00e5ff]"></span><span class="text-on-surface text-[11px]">Valle #0 SCZ (295m)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#38bdf8]"></span><span class="text-on-surface text-[11px]">Sub #1 Equipetrol (240m)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#ff3366]"></span><span class="text-on-surface text-[11px]">Valle #2 Plan 3000 (340m)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#34d399]"></span><span class="text-on-surface text-[11px]">Valle #7 Cochabamba (380m)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#818cf8]"></span><span class="text-on-surface text-[11px]">Valle #5 La Paz (430m)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#64748b]"></span><span class="text-outline text-[11px]">Picos Ruido (>2500m)</span></div>
                `;
            }
            if (legendGmm) {
                legendGmm.innerHTML = `
                    <span class="text-[10px] text-emerald-400 uppercase tracking-wider block font-bold mb-1">GMM Gaussianas (&pi;)</span>
                    <div class="legend-item"><span class="legend-dot bg-[#00e5ff]"></span><span class="text-on-surface text-[11px]">SCZ Casco (&pi;=0.42)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#ff3366]"></span><span class="text-on-surface text-[11px]">Plan 3000 (&pi;=0.28)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#34d399]"></span><span class="text-on-surface text-[11px]">Cochabamba (&pi;=0.18)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#818cf8]"></span><span class="text-on-surface text-[11px]">La Paz / El Alto (&pi;=0.12)</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#64748b]"></span><span class="text-outline text-[11px]">Dispersión (>3&sigma;)</span></div>
                `;
            }
            if (legendWard) {
                legendWard.innerHTML = `
                    <span class="text-[10px] text-purple-400 uppercase tracking-wider block font-bold mb-1">Ward Macro-Clusters</span>
                    <div class="legend-item"><span class="legend-dot bg-[#ff3366]"></span><span class="text-on-surface text-[11px]">Macro A: Casco SCZ</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#fbbf24]"></span><span class="text-on-surface text-[11px]">Macro B: CBBA & Plan 3000</span></div>
                    <div class="legend-item"><span class="legend-dot bg-[#34d399]"></span><span class="text-on-surface text-[11px]">Macro C: La Paz & Perif.</span></div>
                `;
            }
        }
    }

    // Centros urbanos y distritos policiales predefinidos con inclinación 3D oblicua táctica
    const VIEWPORTS = {
        'global': { center: [0, 20], zoom: 1.8, pitch: 0, bearing: 0 },
        // Bolivia (Primario) - Perspectiva orbital y relieve andino
        'bolivia': { center: [-64.9, -16.5], zoom: 5.2, pitch: 32, bearing: -6 },
        'santa cruz': { center: [-63.1821, -17.7833], zoom: 12.8, pitch: 52, bearing: -22 },
        'la paz': { center: [-68.1336, -16.4958], zoom: 13.2, pitch: 56, bearing: 28 },
        'el alto': { center: [-68.1630, -16.5075], zoom: 13.0, pitch: 50, bearing: 14 },
        'cochabamba': { center: [-66.1570, -17.3935], zoom: 13.0, pitch: 52, bearing: -15 },
        'viacha': { center: [-68.3000, -16.6533], zoom: 14.2, pitch: 54, bearing: 10 },
        'riberalta': { center: [-66.0631, -11.0042], zoom: 13.5, pitch: 48, bearing: -8 },
        'punata': { center: [-65.8333, -17.5500], zoom: 14.0, pitch: 50, bearing: 5 },
        'warnes': { center: [-63.1667, -17.5167], zoom: 13.5, pitch: 48, bearing: -12 },
        // Chicago (Benchmark Secundario) - Perspectiva 3D corridor urbano
        'chicago': { center: [-87.6298, 41.8781], zoom: 11.0, pitch: 45, bearing: -18 },
        'the loop': { center: [-87.6231, 41.8818], zoom: 14.0, pitch: 58, bearing: -26 },
        'west side': { center: [-87.7200, 41.8750], zoom: 13.4, pitch: 52, bearing: 12 },
        'south side': { center: [-87.6400, 41.7750], zoom: 13.4, pitch: 52, bearing: -15 },
        'north side': { center: [-87.6500, 41.9400], zoom: 13.4, pitch: 50, bearing: 18 }
    };

    // Configuración inicial de cámara según contexto
    const initVP = activeContext === 'chicago' ? VIEWPORTS['chicago'] : VIEWPORTS['bolivia'];

    // 1. Inicializar Mapa con Proyección Globe 3D
    map = new maplibregl.Map({
        container: 'map-container',
        style: 'https://tiles.openfreemap.org/styles/liberty',
        center: initVP.center,
        zoom: initVP.zoom,
        pitch: initVP.pitch,
        bearing: initVP.bearing || 0,
        minZoom: 1.5,
        maxZoom: 18,
        projection: {
            type: 'globe'
        }
    });

    map.addControl(new maplibregl.NavigationControl({
        visualizePitch: true,
        showCompass: true
    }), 'bottom-right');

    map.addControl(new maplibregl.ScaleControl({
        maxWidth: 120,
        unit: 'metric'
    }), 'bottom-left');

    // 2. Evento Load: Atmósfera Orbital Crepuscular y Capas Vectoriales
    map.on('load', () => {
        if (typeof map.setSky === 'function') {
            map.setSky({
                'sky-color': '#020617',          // Espacio profundo medianoche
                'sky-horizon-blend': 0.72,       // Transición gradual
                'horizon-color': '#002f54',      // Resplandor cian atmosférico orbital
                'horizon-fog-blend': 0.86,       // Difuminado de horizonte
                'fog-color': '#020817',          // Niebla de superficie oscura
                'fog-ground-blend': 0.42         // Acoplamiento suave con el terreno
            });
        }

        loadGeojsonData();
    });

    // 3. Cargar datos GeoJSON desde el backend Flask
    function loadGeojsonData() {
        const cat = filterCategoryEl ? filterCategoryEl.value : 'todos';
        const city = filterCityEl ? filterCityEl.value : 'todas';

        const url = `/api/v1/webgis/geojson?ctx=${encodeURIComponent(activeContext)}&categoria=${encodeURIComponent(cat)}&ciudad=${encodeURIComponent(city)}`;

        fetch(url)
            .then(res => res.json())
            .then(data => {
                currentGeojson = data;

                if (statTotalEl) {
                    statTotalEl.textContent = data.total || 0;
                }

                if (map.getSource('webgis-events')) {
                    map.getSource('webgis-events').setData(data);
                }
                if (map.getSource('webgis-events-raw')) {
                    map.getSource('webgis-events-raw').setData(data);
                }
                if (!map.getSource('webgis-events')) {
                    setupGeojsonLayers(data);
                }
            })
            .catch(err => console.error("[WebGIS] Error cargando GeoJSON:", err));
    }

    // 4. Capas Vectoriales de Clustering WebGL
    function setupGeojsonLayers(geojson) {
        // 1. Fuente agrupada con WebGL Clustering (Halos con números)
        map.addSource('webgis-events', {
            type: 'geojson',
            data: geojson,
            cluster: true,
            clusterMaxZoom: 14,
            clusterRadius: 50
        });

        // 2. Fuente no agrupada para visualización continua de puntos individuales a cualquier zoom
        map.addSource('webgis-events-raw', {
            type: 'geojson',
            data: geojson,
            cluster: false
        });

        // Halo concéntrico exterior de clústeres
        map.addLayer({
            id: 'clusters-halo',
            type: 'circle',
            source: 'webgis-events',
            filter: ['has', 'point_count'],
            paint: {
                'circle-color': [
                    'step',
                    ['get', 'point_count'],
                    'rgba(0, 229, 255, 0.25)',     // < 5 incidentes: Cyan
                    5, 'rgba(251, 191, 36, 0.25)',  // 5 a 15: Ámbar
                    15, 'rgba(255, 51, 102, 0.3)'   // > 15: Hotspot
                ],
                'circle-radius': [
                    'step',
                    ['get', 'point_count'],
                    22,
                    5, 30,
                    15, 42
                ],
                'circle-blur': 0.2
            }
        });

        // Núcleo sólido interior
        map.addLayer({
            id: 'clusters-core',
            type: 'circle',
            source: 'webgis-events',
            filter: ['has', 'point_count'],
            paint: {
                'circle-color': [
                    'step',
                    ['get', 'point_count'],
                    '#00e5ff',
                    5, '#fbbf24',
                    15, '#ff3366'
                ],
                'circle-radius': [
                    'step',
                    ['get', 'point_count'],
                    13,
                    5, 17,
                    15, 23
                ],
                'circle-stroke-width': 2,
                'circle-stroke-color': '#0f131c'
            }
        });

        // Conteo numérico de incidentes
        map.addLayer({
            id: 'cluster-count',
            type: 'symbol',
            source: 'webgis-events',
            filter: ['has', 'point_count'],
            layout: {
                'text-field': '{point_count_abbreviated}',
                'text-font': ['Noto Sans Bold'],
                'text-size': 12
            },
            paint: {
                'text-color': '#0f131c'
            }
        });

        // 3. Fuentes GeoJSON de Elipses de Confianza GMM 2-sigma y Centroides
        map.addSource('gmm-ellipses-source', {
            type: 'geojson',
            data: generateGmmEllipsesGeojson(activeContext)
        });

        map.addSource('gmm-centroids-source', {
            type: 'geojson',
            data: generateGmmCentroidsGeojson(activeContext)
        });

        // Capa de Relleno Translúcido de Elipses GMM 2-sigma
        map.addLayer({
            id: 'gmm-ellipses-fill',
            type: 'fill',
            source: 'gmm-ellipses-source',
            paint: {
                'fill-color': ['get', 'color'],
                'fill-opacity': currentClusterMode === 'gmm' ? 0.18 : 0.0,
                'fill-opacity-transition': { duration: 600, delay: 0 }
            }
        });

        // Capa de Borde Geodésico Segmentado de Elipses GMM 2-sigma
        map.addLayer({
            id: 'gmm-ellipses-line',
            type: 'line',
            source: 'gmm-ellipses-source',
            paint: {
                'line-color': ['get', 'color'],
                'line-width': 2.2,
                'line-dasharray': [3, 2],
                'line-opacity': currentClusterMode === 'gmm' ? 0.85 : 0.0,
                'line-opacity-transition': { duration: 600, delay: 0 }
            }
        });

        // Marcadores individuales con paleta unificada para Bolivia y Chicago
        map.addLayer({
            id: 'unclustered-point',
            type: 'circle',
            source: 'webgis-events',
            filter: ['!', ['has', 'point_count']],
            layout: { 'visibility': 'visible' },
            paint: {
                'circle-color-transition': { duration: 550, delay: 0 },
                'circle-radius-transition': { duration: 550, delay: 0 },
                'circle-opacity-transition': { duration: 550, delay: 0 },
                'circle-stroke-color-transition': { duration: 550, delay: 0 },
                'circle-stroke-width-transition': { duration: 550, delay: 0 },
                'circle-color': [
                    'match',
                    ['get', 'category'],
                    // Bolivia
                    'Robo Agravado / Asalto', '#ff3366',
                    'Agresión Física y Lesiones', '#fbbf24',
                    'Hurto / Descuidismo', '#00e5ff',
                    'Homicidio / Asesinato', '#ff0033',
                    'Narcotráfico / Drogas', '#34d399',
                    // Chicago
                    'THEFT', '#00e5ff',
                    'BATTERY', '#ff3366',
                    'CRIMINAL DAMAGE', '#fbbf24',
                    'ASSAULT', '#ff5c8a',
                    'DECEPTIVE PRACTICE', '#9d4edd',
                    'ROBBERY', '#f97316',
                    'MOTOR VEHICLE THEFT', '#38bdf8',
                    'NARCOTICS', '#34d399',
                    'WEAPONS VIOLATION', '#ef4444',
                    /* Default */ '#38bdf8'
                ],
                'circle-radius': 7.5,
                'circle-stroke-width': 2,
                'circle-stroke-color': '#ffffff'
            }
        });

        // Marcadores individuales continuos (Modo Disperso / No Supervisado a cualquier zoom)
        map.addLayer({
            id: 'raw-points',
            type: 'circle',
            source: 'webgis-events-raw',
            layout: { 'visibility': 'none' },
            paint: {
                'circle-color-transition': { duration: 550, delay: 0 },
                'circle-radius-transition': { duration: 550, delay: 0 },
                'circle-opacity-transition': { duration: 550, delay: 0 },
                'circle-stroke-color-transition': { duration: 550, delay: 0 },
                'circle-stroke-width-transition': { duration: 550, delay: 0 },
                'circle-color': [
                    'match',
                    ['get', 'category'],
                    // Bolivia
                    'Robo Agravado / Asalto', '#ff3366',
                    'Agresión Física y Lesiones', '#fbbf24',
                    'Hurto / Descuidismo', '#00e5ff',
                    'Homicidio / Asesinato', '#ff0033',
                    'Narcotráfico / Drogas', '#34d399',
                    // Chicago
                    'THEFT', '#00e5ff',
                    'BATTERY', '#ff3366',
                    'CRIMINAL DAMAGE', '#fbbf24',
                    'ASSAULT', '#ff5c8a',
                    'DECEPTIVE PRACTICE', '#9d4edd',
                    'ROBBERY', '#f97316',
                    'MOTOR VEHICLE THEFT', '#38bdf8',
                    'NARCOTICS', '#34d399',
                    'WEAPONS VIOLATION', '#ef4444',
                    /* Default */ '#38bdf8'
                ],
                'circle-radius': [
                    'interpolate',
                    ['linear'],
                    ['zoom'],
                    2, 4.5,
                    5, 6.0,
                    10, 7.5,
                    14, 9.0
                ],
                'circle-stroke-width': 1.8,
                'circle-stroke-color': '#ffffff'
            }
        });

        // Capa de Etiquetas de Centroides y Ponderación Mixtura GMM (π)
        map.addLayer({
            id: 'gmm-centroids-labels',
            type: 'symbol',
            source: 'gmm-centroids-source',
            layout: {
                'text-field': '{label}',
                'text-font': ['Noto Sans Bold'],
                'text-size': 11,
                'text-offset': [0, 0],
                'text-anchor': 'center',
                'text-allow-overlap': true
            },
            paint: {
                'text-color': '#ffffff',
                'text-halo-color': '#070b12',
                'text-halo-width': 2.5,
                'text-opacity': currentClusterMode === 'gmm' ? 0.95 : 0.0,
                'text-opacity-transition': { duration: 600, delay: 0 }
            }
        });

        // Aplicar estilo de color según el modo algorítmico activo
        applyClusterStyle(currentClusterMode);
        setClusteringMode(isClusteringEnabled);

        // Expansión suave al hacer clic en clúster
        map.on('click', 'clusters-core', (e) => {
            const features = map.queryRenderedFeatures(e.point, { layers: ['clusters-core'] });
            if (!features.length) return;

            const clusterId = features[0].properties.cluster_id;
            map.getSource('webgis-events').getClusterExpansionZoom(clusterId, (err, zoom) => {
                if (err) return;

                map.easeTo({
                    center: features[0].geometry.coordinates,
                    zoom: zoom + 0.8,
                    pitch: Math.min(50, map.getPitch() + 15),
                    duration: 1000
                });
            });
        });

        // Función unificada para desplegar el Popup táctico enriquecido (DBSCAN, OPTICS, GMM, Ward)
        function handlePointClick(e) {
            const feature = e.features[0];
            const coords = feature.geometry.coordinates.slice();
            const props = feature.properties;

            while (Math.abs(e.lngLat.lng - coords[0]) > 180) {
                coords[0] += e.lngLat.lng > coords[0] ? 360 : -360;
            }

            const dbscanBadgeClass = (props.dbscan === -1 || props.dbscan === '-1')
                ? 'bg-slate-700/60 text-slate-300 border-slate-600'
                : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';

            const hdbscanBadgeClass = (props.hdbscan === -1 || props.hdbscan === '-1')
                ? 'bg-slate-700/60 text-slate-300 border-slate-600'
                : 'bg-teal-500/20 text-teal-300 border-teal-500/40';

            const opticsBadgeClass = (props.optics === -1 || props.optics === '-1')
                ? 'bg-slate-700/60 text-slate-300 border-slate-600'
                : 'bg-amber-500/20 text-amber-300 border-amber-500/40';

            const gmmBadgeClass = (props.gmm === -1 || props.gmm === '-1')
                ? 'bg-slate-700/60 text-slate-300 border-slate-600'
                : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';

            const wardBadgeClass = props.ward === 'A'
                ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                : (props.ward === 'B'
                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                    : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40');

            const popupContent = `
                <div class="news-popup-container font-data-code">
                    <span class="news-popup-category">${props.category || 'INCIDENTE'}</span>
                    <h4 class="news-popup-title font-sans">${props.title}</h4>
                    <div class="news-popup-meta text-[11px] space-y-1">
                        <div><span class="text-outline uppercase text-[10px] tracking-wider">ZONA:</span> <strong class="text-on-surface">${props.zone || props.city}</strong></div>
                        <div><span class="text-outline uppercase text-[10px] tracking-wider">FECHA:</span> <strong class="text-on-surface">${props.date}</strong></div>
                        <div><span class="text-outline uppercase text-[10px] tracking-wider">CIUDAD:</span> <strong class="text-on-surface">${props.city}</strong></div>
                        <div><span class="text-outline uppercase text-[10px] tracking-wider">FUENTE:</span> <strong class="text-primary-container">${props.source}</strong></div>
                        
                        <!-- Badges No Supervisados: DBSCAN, HDBSCAN, OPTICS, GMM & Ward -->
                        <div class="pt-2 mt-1 border-t border-outline-variant/60 flex flex-col gap-1">
                            <div class="flex items-center gap-1.5">
                                <span class="px-1.5 py-0.5 rounded text-[10px] font-bold border ${dbscanBadgeClass}">
                                    ${props.dbscan_label || ('DBSCAN: Hotspot #' + props.dbscan)}
                                </span>
                            </div>
                            <div class="flex items-center gap-1.5">
                                <span class="px-1.5 py-0.5 rounded text-[10px] font-bold border ${hdbscanBadgeClass}">
                                    ${props.hdbscan_label || ('HDBSCAN: Cluster #' + props.hdbscan)}
                                </span>
                                ${props.hdbscan_persistence ? `<span class="text-[9px] text-teal-400 font-bold">(&lambda;=${props.hdbscan_persistence})</span>` : ''}
                            </div>
                            <div class="flex items-center gap-1.5">
                                <span class="px-1.5 py-0.5 rounded text-[10px] font-bold border ${opticsBadgeClass}">
                                    ${props.optics_valley || ('OPTICS: Valle #' + props.optics)}
                                </span>
                                ${props.reach_depth_m ? `<span class="text-[9px] text-outline">(&le; ${props.reach_depth_m}m)</span>` : ''}
                            </div>
                            <div class="flex items-center gap-1.5">
                                <span class="px-1.5 py-0.5 rounded text-[10px] font-bold border ${gmmBadgeClass}">
                                    ${props.gmm_label || ('GMM: Componente #' + props.gmm)}
                                </span>
                                ${props.gmm_prob ? `<span class="text-[9px] text-emerald-400 font-bold">(${props.gmm_prob}%)</span>` : ''}
                            </div>
                            <div class="flex items-center gap-1.5">
                                <span class="px-1.5 py-0.5 rounded text-[10px] font-bold border ${wardBadgeClass}">
                                    ${props.ward_label || ('Ward: Macro ' + props.ward)}
                                </span>
                            </div>
                        </div>
                    </div>
                    ${props.url && props.url !== '#' ? `
                        <a href="${props.url}" target="_blank" rel="noopener noreferrer" class="news-popup-link mt-2 text-xs">
                            <span>Ver Registro Oficial</span>
                            <span class="material-symbols-outlined" style="font-size: 14px;">open_in_new</span>
                        </a>
                    ` : ''}
                </div>
            `;

            new maplibregl.Popup({ offset: 12, closeButton: true })
                .setLngLat(coords)
                .setHTML(popupContent)
                .addTo(map);
        }

        map.on('click', 'unclustered-point', handlePointClick);
        map.on('click', 'raw-points', handlePointClick);

        // Interacción Popup Táctico para Elipses de Confianza GMM 2-sigma
        map.on('click', 'gmm-ellipses-fill', (e) => {
            if (currentClusterMode !== 'gmm') return;
            const features = map.queryRenderedFeatures(e.point, { layers: ['gmm-ellipses-fill'] });
            if (!features.length) return;
            const props = features[0].properties;

            const popupContent = `
                <div class="news-popup-container font-data-code">
                    <div class="flex items-center gap-1.5 mb-1.5">
                        <span class="w-2.5 h-2.5 rounded-full inline-block" style="background-color: ${props.color};"></span>
                        <span class="text-xs font-bold text-white uppercase">${props.name}</span>
                    </div>
                    <div class="text-[11px] text-emerald-400 font-semibold mb-2 flex items-center gap-1">
                        <span class="material-symbols-outlined text-[13px]">tune</span>
                        <span>Elipse de Confianza 2&sigma; (Masa: 86.5%)</span>
                    </div>
                    <div class="news-popup-meta text-[11px] space-y-1 text-slate-300">
                        <div><span class="text-outline uppercase text-[10px] tracking-wider">PESO MIXTURA (&pi;):</span> <strong class="text-white">${props.weight_percent || (Number(props.weight) * 100).toFixed(0)}%</strong></div>
                        <div><span class="text-outline uppercase text-[10px] tracking-wider">SEMI-EJE MAYOR (a):</span> <strong class="text-white">${Number(props.a).toLocaleString()} m</strong></div>
                        <div><span class="text-outline uppercase text-[10px] tracking-wider">SEMI-EJE MENOR (b):</span> <strong class="text-white">${Number(props.b).toLocaleString()} m</strong></div>
                        <div><span class="text-outline uppercase text-[10px] tracking-wider">ORIENTACIÓN AUTOVECTOR (&theta;):</span> <strong class="text-white">${props.angle}&deg;</strong></div>
                        <div><span class="text-outline uppercase text-[10px] tracking-wider">CENTROIDE (&mu;):</span> <strong class="text-slate-400 font-mono text-[10px]">[${Number(props.center_lng).toFixed(4)}, ${Number(props.center_lat).toFixed(4)}]</strong></div>
                        
                        <div class="pt-2 mt-1 border-t border-slate-700/60 text-[10px] text-slate-400 leading-normal">
                            ${props.description}
                        </div>
                    </div>
                </div>
            `;

            new maplibregl.Popup({ offset: 10, closeButton: true })
                .setLngLat(e.lngLat)
                .setHTML(popupContent)
                .addTo(map);
        });

        map.on('mouseenter', 'clusters-core', () => map.getCanvas().style.cursor = 'pointer');
        map.on('mouseleave', 'clusters-core', () => map.getCanvas().style.cursor = '');
        map.on('mouseenter', 'unclustered-point', () => map.getCanvas().style.cursor = 'pointer');
        map.on('mouseleave', 'unclustered-point', () => map.getCanvas().style.cursor = '');
        map.on('mouseenter', 'raw-points', () => map.getCanvas().style.cursor = 'pointer');
        map.on('mouseleave', 'raw-points', () => map.getCanvas().style.cursor = '');
        map.on('mouseenter', 'gmm-ellipses-fill', () => {
            if (currentClusterMode === 'gmm') map.getCanvas().style.cursor = 'pointer';
        });
        map.on('mouseleave', 'gmm-ellipses-fill', () => {
            if (currentClusterMode === 'gmm') map.getCanvas().style.cursor = '';
        });
    }

    // Helper para sincronizar propiedades visuales tanto en puntos de clúster como en puntos individuales continuos
    function setPointsPaint(property, value) {
        if (!map) return;
        if (map.getLayer('unclustered-point')) {
            map.setPaintProperty('unclustered-point', property, value);
        }
        if (map.getLayer('raw-points')) {
            map.setPaintProperty('raw-points', property, value);
        }
    }

    // Conmutador del modo de visualización: Agrupación WebGL (halos numéricos) vs Puntos Individuales
    function setClusteringMode(enabled) {
        isClusteringEnabled = enabled;

        const clusterVis = enabled ? 'visible' : 'none';
        const rawVis = enabled ? 'none' : 'visible';

        if (map && map.getStyle()) {
            if (map.getLayer('clusters-halo')) map.setLayoutProperty('clusters-halo', 'visibility', clusterVis);
            if (map.getLayer('clusters-core')) map.setLayoutProperty('clusters-core', 'visibility', clusterVis);
            if (map.getLayer('cluster-count')) map.setLayoutProperty('cluster-count', 'visibility', clusterVis);
            if (map.getLayer('unclustered-point')) map.setLayoutProperty('unclustered-point', 'visibility', clusterVis);
            if (map.getLayer('raw-points')) map.setLayoutProperty('raw-points', 'visibility', rawVis);
        }

        const clusterBadge = document.getElementById('cluster-toggle-badge');
        const clusterIcon = document.getElementById('cluster-toggle-icon');

        if (btnToggleCluster && clusterBadge && clusterIcon) {
            if (enabled) {
                btnToggleCluster.classList.add('active');
                clusterBadge.innerHTML = '<span class="size-1.5 rounded-full bg-emerald-400 inline-block mr-1"></span>AGRUPADO';
                clusterBadge.className = 'hud-action-badge';
                clusterIcon.textContent = 'bubble_chart';
            } else {
                btnToggleCluster.classList.remove('active');
                clusterBadge.innerHTML = '<span class="size-1.5 rounded-full bg-cyan-400 inline-block mr-1"></span>INDIVIDUAL';
                clusterBadge.className = 'hud-action-badge bg-cyan-500/20 text-cyan-300 border border-cyan-500/40';
                clusterIcon.textContent = 'scatter_plot';
            }
        }
    }

    // 5. Aplicar Estilos de Shaders Dinámicos (Categoría vs DBSCAN vs OPTICS vs GMM vs Ward)
    function applyClusterStyle(mode) {
        if (!map || (!map.getLayer('unclustered-point') && !map.getLayer('raw-points'))) return;

        if (mode === 'category') {
            setPointsPaint('circle-color', [
                'match',
                ['get', 'category'],
                // Bolivia
                'Robo Agravado / Asalto', '#ff3366',
                'Agresión Física y Lesiones', '#fbbf24',
                'Hurto / Descuidismo', '#00e5ff',
                'Homicidio / Asesinato', '#ff0033',
                'Narcotráfico / Drogas', '#34d399',
                // Chicago
                'THEFT', '#00e5ff',
                'BATTERY', '#ff3366',
                'CRIMINAL DAMAGE', '#fbbf24',
                'ASSAULT', '#ff5c8a',
                'DECEPTIVE PRACTICE', '#9d4edd',
                'ROBBERY', '#f97316',
                'MOTOR VEHICLE THEFT', '#38bdf8',
                'NARCOTICS', '#34d399',
                'WEAPONS VIOLATION', '#ef4444',
                /* Default */ '#38bdf8'
            ]);
            setPointsPaint('circle-radius', [
                'interpolate', ['linear'], ['zoom'],
                2, 4.5,
                5, 6.0,
                10, 7.5,
                14, 9.0
            ]);
            setPointsPaint('circle-opacity', 0.95);
            setPointsPaint('circle-stroke-color', '#ffffff');
            setPointsPaint('circle-stroke-width', 1.8);

        } else if (mode === 'dbscan') {
            setPointsPaint('circle-color', [
                'case',
                ['==', ['get', 'dbscan'], -1], '#64748b',
                ['coalesce', ['get', 'dbscan_color'], '#00e5ff']
            ]);

            setPointsPaint('circle-radius', [
                'case',
                ['==', ['get', 'dbscan'], -1],
                ['interpolate', ['linear'], ['zoom'], 2, 3.0, 8, 4.8, 14, 6.5],
                ['interpolate', ['linear'], ['zoom'], 2, 5.0, 8, 8.5, 14, 11.0]
            ]);
            setPointsPaint('circle-opacity', [
                'case',
                ['==', ['get', 'dbscan'], -1], 0.32,
                0.95
            ]);
            setPointsPaint('circle-stroke-color', [
                'case',
                ['==', ['get', 'dbscan'], -1], '#475569',
                '#ffffff'
            ]);
            setPointsPaint('circle-stroke-width', [
                'case',
                ['==', ['get', 'dbscan'], -1], 1.0,
                2.2
            ]);

        } else if (mode === 'hdbscan') {
            // Modo HDBSCAN: Clusters Jerárquicos de Densidad Variable y Ruido
            setPointsPaint('circle-color', [
                'case',
                ['==', ['get', 'hdbscan'], -1], '#64748b',
                ['coalesce', ['get', 'hdbscan_color'], '#34d399']
            ]);

            setPointsPaint('circle-radius', [
                'case',
                ['==', ['get', 'hdbscan'], -1],
                ['interpolate', ['linear'], ['zoom'], 2, 3.0, 8, 4.8, 14, 6.5],
                ['interpolate', ['linear'], ['zoom'], 2, 5.0, 8, 8.5, 14, 11.0]
            ]);
            setPointsPaint('circle-opacity', [
                'case',
                ['==', ['get', 'hdbscan'], -1], 0.32,
                0.95
            ]);
            setPointsPaint('circle-stroke-color', [
                'case',
                ['==', ['get', 'hdbscan'], -1], '#475569',
                '#ffffff'
            ]);
            setPointsPaint('circle-stroke-width', [
                'case',
                ['==', ['get', 'hdbscan'], -1], 1.0,
                2.2
            ]);

        } else if (mode === 'optics') {
            setPointsPaint('circle-color', [
                'case',
                ['==', ['get', 'optics'], -1], '#64748b',
                ['coalesce', ['get', 'optics_color'], '#fbbf24']
            ]);

            setPointsPaint('circle-radius', [
                'case',
                ['==', ['get', 'optics'], -1],
                ['interpolate', ['linear'], ['zoom'], 2, 3.0, 8, 4.8, 14, 6.5],
                ['interpolate', ['linear'], ['zoom'], 2, 5.0, 8, 8.5, 14, 11.0]
            ]);
            setPointsPaint('circle-opacity', [
                'case',
                ['==', ['get', 'optics'], -1], 0.32,
                0.95
            ]);
            setPointsPaint('circle-stroke-color', [
                'case',
                ['==', ['get', 'optics'], -1], '#334155',
                '#ffffff'
            ]);
            setPointsPaint('circle-stroke-width', [
                'case',
                ['==', ['get', 'optics'], -1], 1.0,
                2.2
            ]);

        } else if (mode === 'gmm') {
            // Modo 4: Componentes Gaussianas y Elipses Multivariantes GMM
            setPointsPaint('circle-color', [
                'case',
                ['==', ['get', 'gmm'], -1], '#64748b',
                ['coalesce', ['get', 'gmm_color'], '#00e5ff']
            ]);

            setPointsPaint('circle-radius', [
                'case',
                ['==', ['get', 'gmm'], -1],
                ['interpolate', ['linear'], ['zoom'], 2, 3.2, 8, 5.0, 14, 6.8],
                ['interpolate', ['linear'], ['zoom'], 2, 5.2, 8, 8.5, 14, 11.0]
            ]);
            setPointsPaint('circle-opacity', [
                'case',
                ['==', ['get', 'gmm'], -1], 0.35,
                0.95
            ]);
            setPointsPaint('circle-stroke-color', [
                'case',
                ['==', ['get', 'gmm'], -1], '#334155',
                '#ffffff'
            ]);
            setPointsPaint('circle-stroke-width', [
                'case',
                ['==', ['get', 'gmm'], -1], 1.0,
                2.2
            ]);

        } else if (mode === 'ward') {
            // Modo 5: Macro-Clusters Jerárquicos Aglomerativos (Ward Linkage k=3)
            setPointsPaint('circle-color', [
                'coalesce', ['get', 'ward_color'], '#94a3b8'
            ]);

            setPointsPaint('circle-radius', [
                'interpolate', ['linear'], ['zoom'],
                2, 4.8,
                5, 6.5,
                10, 8.2,
                14, 10.0
            ]);
            setPointsPaint('circle-opacity', 0.95);
            setPointsPaint('circle-stroke-color', '#ffffff');
            setPointsPaint('circle-stroke-width', 2.0);
        }
    }

    // 6. Conmutación de Modo Algorítmico (Delito / DBSCAN / HDBSCAN / OPTICS / GMM / Ward)
    function setClusterMode(newMode) {
        currentClusterMode = newMode;

        // Sincronizar tema de bordes y resplandores en el viewport
        if (viewportEl) {
            viewportEl.setAttribute('data-algo-theme', newMode);
        }

        [btnModeCategory, btnModeDbscan, btnModeHdbscan, btnModeOptics, btnModeGmm, btnModeWard].forEach(b => {
            if (b) b.classList.remove('active');
        });

        if (newMode === 'category' && btnModeCategory) btnModeCategory.classList.add('active');
        if (newMode === 'dbscan' && btnModeDbscan) btnModeDbscan.classList.add('active');
        if (newMode === 'hdbscan' && btnModeHdbscan) btnModeHdbscan.classList.add('active');
        if (newMode === 'optics' && btnModeOptics) btnModeOptics.classList.add('active');
        if (newMode === 'gmm' && btnModeGmm) btnModeGmm.classList.add('active');
        if (newMode === 'ward' && btnModeWard) btnModeWard.classList.add('active');

        if (activeModeLabel) {
            activeModeLabel.textContent = newMode === 'category' ? 'DELITOS' : newMode.toUpperCase();
            if (newMode === 'category') activeModeLabel.className = 'text-primary-container font-semibold';
            else if (newMode === 'dbscan') activeModeLabel.className = 'text-cyan-400 font-bold';
            else if (newMode === 'hdbscan') activeModeLabel.className = 'text-teal-400 font-bold';
            else if (newMode === 'optics') activeModeLabel.className = 'text-amber-400 font-bold';
            else if (newMode === 'gmm') activeModeLabel.className = 'text-emerald-400 font-bold';
            else if (newMode === 'ward') activeModeLabel.className = 'text-purple-400 font-bold';
        }

        const legendModeTitle = document.getElementById('legend-active-mode-title');
        if (legendModeTitle) {
            legendModeTitle.textContent = newMode === 'category' ? 'DELITOS' : newMode.toUpperCase();
        }

        if (legendCategory) legendCategory.classList.toggle('hidden', newMode !== 'category');
        if (legendDbscan) legendDbscan.classList.toggle('hidden', newMode !== 'dbscan');
        if (legendHdbscan) legendHdbscan.classList.toggle('hidden', newMode !== 'hdbscan');
        if (legendOptics) legendOptics.classList.toggle('hidden', newMode !== 'optics');
        if (legendGmm) legendGmm.classList.toggle('hidden', newMode !== 'gmm');
        if (legendWard) legendWard.classList.toggle('hidden', newMode !== 'ward');

        // Transición animada de elipses de covarianza y etiquetas GMM
        if (map && map.getStyle()) {
            const isGmm = newMode === 'gmm';
            if (map.getLayer('gmm-ellipses-fill')) {
                map.setPaintProperty('gmm-ellipses-fill', 'fill-opacity', isGmm ? 0.18 : 0.0);
            }
            if (map.getLayer('gmm-ellipses-line')) {
                map.setPaintProperty('gmm-ellipses-line', 'line-opacity', isGmm ? 0.85 : 0.0);
            }
            if (map.getLayer('gmm-centroids-labels')) {
                map.setPaintProperty('gmm-centroids-labels', 'text-opacity', isGmm ? 0.95 : 0.0);
            }
        }

        applyClusterStyle(newMode);

        // Auto-switch inteligente: Si se selecciona un modelo no supervisado (DBSCAN, HDBSCAN, OPTICS, GMM, Ward),
        // deshabilitar la agrupación WebGL para revelar todos los puntos individuales en el globo
        if (newMode === 'category') {
            setClusteringMode(true);
        } else {
            setClusteringMode(false);
        }
    }

    if (btnModeCategory) btnModeCategory.addEventListener('click', () => setClusterMode('category'));
    if (btnModeDbscan) btnModeDbscan.addEventListener('click', () => setClusterMode('dbscan'));
    if (btnModeHdbscan) btnModeHdbscan.addEventListener('click', () => setClusterMode('hdbscan'));
    if (btnModeOptics) btnModeOptics.addEventListener('click', () => setClusterMode('optics'));
    if (btnModeGmm) btnModeGmm.addEventListener('click', () => setClusterMode('gmm'));
    if (btnModeWard) btnModeWard.addEventListener('click', () => setClusterMode('ward'));

    // 5. Conmutación Dinámica de Dataset en Tiempo Real (Bolivia ↔ Chicago)
    function switchContext(newCtx) {
        if (activeContext === newCtx) return;
        activeContext = newCtx;

        // Actualizar estado visual de los botones de conmutación
        if (btnSwitchBolivia && btnSwitchChicago) {
            btnSwitchBolivia.classList.toggle('active', newCtx !== 'chicago');
            btnSwitchChicago.classList.toggle('active', newCtx === 'chicago');
        }

        // Actualizar URL sin recargar la página (evita ir a la página principal)
        const newUrl = new URL(window.location.href);
        newUrl.searchParams.set('ctx', newCtx);
        window.history.pushState({ ctx: newCtx }, '', newUrl.toString());

        // Actualizar badge contextual en el HUD top-left
        const hudBadgeEl = document.querySelector('.hud-top-left .text-outline.font-data-code');
        if (hudBadgeEl) {
            hudBadgeEl.textContent = newCtx === 'chicago' ? 'US CHICAGO' : 'BO BOLIVIA';
        }

        // Vuelo suave de cámara al centroide del contexto seleccionado con perspectiva 3D
        const vp = newCtx === 'chicago' ? VIEWPORTS['chicago'] : VIEWPORTS['bolivia'];
        map.flyTo({
            center: vp.center,
            zoom: vp.zoom,
            pitch: vp.pitch,
            bearing: vp.bearing || 0,
            duration: 2200,
            curve: 1.42,
            easing: (t) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
            essential: true
        });

        // Actualizar fuentes GeoJSON de elipses y centroides GMM
        if (map.getSource('gmm-ellipses-source')) {
            map.getSource('gmm-ellipses-source').setData(generateGmmEllipsesGeojson(newCtx));
        }
        if (map.getSource('gmm-centroids-source')) {
            map.getSource('gmm-centroids-source').setData(generateGmmCentroidsGeojson(newCtx));
        }

        // Actualizar leyendas tácticas y estilos según contexto
        updateLegends(newCtx);
        applyClusterStyle(currentClusterMode);

        // Actualizar metadatos, filtros y capas
        updateMetadataAndFilters(newCtx);
        loadGeojsonData();
        updateBottomDock(newCtx);
    }

    // Actualizar filtros dropdowns desde la API de metadatos
    function updateMetadataAndFilters(ctx) {
        fetch(`/api/v1/webgis/metadata?ctx=${encodeURIComponent(ctx)}`)
            .then(res => res.json())
            .then(meta => {
                if (filterCategoryEl) {
                    filterCategoryEl.innerHTML = '<option value="todos">Todos los Delitos</option>';
                    (meta.categorias || []).forEach(cat => {
                        const opt = document.createElement('option');
                        opt.value = cat.nombre;
                        opt.textContent = `${cat.nombre} (${cat.count})`;
                        filterCategoryEl.appendChild(opt);
                    });
                }
                if (filterCityEl) {
                    filterCityEl.innerHTML = `<option value="todas">${ctx === 'chicago' ? 'Todos los Distritos' : 'Todas las Ciudades'}</option>`;
                    (meta.ciudades || []).forEach(c => {
                        const opt = document.createElement('option');
                        opt.value = c.nombre;
                        opt.textContent = `${c.nombre} (${c.count})`;
                        filterCityEl.appendChild(opt);
                    });
                }
            })
            .catch(err => console.error("[WebGIS] Error actualizando metadatos:", err));
    }

    // Actualizar dock inferior adaptativo según contexto
    function updateBottomDock(ctx) {
        if (!bottomControlsEl) return;

        if (ctx === 'chicago') {
            bottomControlsEl.innerHTML = `
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn" data-city="global" title="Vista Planeta Completo">
                    <span class="material-symbols-outlined text-sm">public</span>
                    <span>Global</span>
                </button>
                <div class="w-[1px] h-4 bg-outline-variant/80 my-auto mx-0.5 shrink-0"></div>
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn active" data-city="chicago" title="Metro Chicago">
                    <span class="material-symbols-outlined text-sm">location_city</span>
                    <span>Chicago</span>
                </button>
                <div class="relative" id="dock-dropdown-wrapper">
                    <button type="button" id="btn-dock-dropdown-toggle" class="btn-tactile hud-dock-btn flex items-center gap-1" title="Explorar Distritos CPD">
                        <span class="material-symbols-outlined text-sm">domain</span>
                        <span id="dock-dropdown-label">Distritos</span>
                        <span class="material-symbols-outlined text-xs transition-transform duration-200" id="dock-dropdown-chevron">expand_less</span>
                    </button>
                    <div id="dock-dropdown-menu" class="hidden absolute bottom-full mb-2 left-1/2 -translate-x-1/2 min-w-[160px] p-1.5 rounded-xl bg-white/95 dark:bg-slate-900/95 border border-slate-300 dark:border-cyan-500/40 text-slate-900 dark:text-slate-100 backdrop-blur-xl shadow-2xl flex flex-col gap-1 z-30 font-data-code text-xs">
                        <button type="button" class="btn-tactile hud-dock-menu-btn hud-city-btn text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2" data-city="the loop" title="Distrito 1 - The Loop">
                            <span class="material-symbols-outlined text-xs text-cyan-700 dark:text-cyan-400">domain</span>
                            <span>The Loop</span>
                        </button>
                        <button type="button" class="btn-tactile hud-dock-menu-btn hud-city-btn text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2" data-city="west side" title="Distrito 11 - West Side (Garfield / Austin)">
                            <span class="material-symbols-outlined text-xs text-amber-700 dark:text-amber-400">warning</span>
                            <span>West Side</span>
                        </button>
                        <button type="button" class="btn-tactile hud-dock-menu-btn hud-city-btn text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2" data-city="south side" title="Distrito 7 - South Side (Englewood)">
                            <span class="material-symbols-outlined text-xs text-rose-700 dark:text-rose-400">near_me</span>
                            <span>South Side</span>
                        </button>
                        <button type="button" class="btn-tactile hud-dock-menu-btn hud-city-btn text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2" data-city="north side" title="Distrito 19 - North Side (Lincoln / Lakeview)">
                            <span class="material-symbols-outlined text-xs text-sky-700 dark:text-sky-400">shield</span>
                            <span>North Side</span>
                        </button>
                    </div>
                </div>
            `;
        } else {
            bottomControlsEl.innerHTML = `
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn" data-city="global" title="Vista Planeta Completo">
                    <span class="material-symbols-outlined text-sm">public</span>
                    <span>Global</span>
                </button>
                <div class="w-[1px] h-4 bg-outline-variant/80 my-auto mx-0.5 shrink-0"></div>
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn active" data-city="bolivia" title="Enfoque Nacional Bolivia">
                    <span class="material-symbols-outlined text-sm">flag</span>
                    <span>Bolivia</span>
                </button>
                <div class="relative" id="dock-dropdown-wrapper">
                    <button type="button" id="btn-dock-dropdown-toggle" class="btn-tactile hud-dock-btn flex items-center gap-1" title="Explorar Ciudades Principales">
                        <span class="material-symbols-outlined text-sm">apartment</span>
                        <span id="dock-dropdown-label">Ciudades</span>
                        <span class="material-symbols-outlined text-xs transition-transform duration-200" id="dock-dropdown-chevron">expand_less</span>
                    </button>
                    <div id="dock-dropdown-menu" class="hidden absolute bottom-full mb-2 left-1/2 -translate-x-1/2 min-w-[160px] p-1.5 rounded-xl bg-white/95 dark:bg-slate-900/95 border border-slate-300 dark:border-cyan-500/40 text-slate-900 dark:text-slate-100 backdrop-blur-xl shadow-2xl flex flex-col gap-1 z-30 font-data-code text-xs">
                        <button type="button" class="btn-tactile hud-dock-menu-btn hud-city-btn text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2" data-city="santa cruz" title="Área Metropolitana Santa Cruz">
                            <span class="material-symbols-outlined text-xs text-cyan-700 dark:text-cyan-400">apartment</span>
                            <span>Santa Cruz</span>
                        </button>
                        <button type="button" class="btn-tactile hud-dock-menu-btn hud-city-btn text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2" data-city="la paz" title="Sede de Gobierno La Paz">
                            <span class="material-symbols-outlined text-xs text-amber-700 dark:text-amber-400">terrain</span>
                            <span>La Paz</span>
                        </button>
                        <button type="button" class="btn-tactile hud-dock-menu-btn hud-city-btn text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2" data-city="el alto" title="Área Metropolitana El Alto">
                            <span class="material-symbols-outlined text-xs text-sky-700 dark:text-sky-400">altitude</span>
                            <span>El Alto</span>
                        </button>
                        <button type="button" class="btn-tactile hud-dock-menu-btn hud-city-btn text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2" data-city="cochabamba" title="Valle Central de Cochabamba">
                            <span class="material-symbols-outlined text-xs text-emerald-700 dark:text-emerald-400">location_on</span>
                            <span>Cochabamba</span>
                        </button>
                        <button type="button" class="btn-tactile hud-dock-menu-btn hud-city-btn text-left px-2.5 py-1.5 rounded-lg flex items-center gap-2" data-city="viacha" title="Municipio de Viacha (Lugar del Hecho)">
                            <span class="material-symbols-outlined text-xs text-purple-700 dark:text-purple-400">explore</span>
                            <span>Viacha</span>
                        </button>
                    </div>
                </div>
            `;
        }
        bindCityButtons();
    }

    // Enlazar clics de botones del dock inferior con soporte para selector desplegable
    function bindCityButtons() {
        const btns = document.querySelectorAll('.hud-city-btn');
        const dropdownToggle = document.getElementById('btn-dock-dropdown-toggle');
        const dropdownMenu = document.getElementById('dock-dropdown-menu');
        const dropdownLabel = document.getElementById('dock-dropdown-label');
        const dropdownChevron = document.getElementById('dock-dropdown-chevron');

        if (dropdownToggle && dropdownMenu) {
            dropdownToggle.onclick = (e) => {
                e.stopPropagation();
                const isOpen = !dropdownMenu.classList.contains('hidden');
                if (isOpen) {
                    dropdownMenu.classList.add('hidden');
                    if (dropdownChevron) dropdownChevron.style.transform = 'rotate(0deg)';
                } else {
                    dropdownMenu.classList.remove('hidden');
                    if (dropdownChevron) dropdownChevron.style.transform = 'rotate(180deg)';
                }
            };
        }

        btns.forEach(btn => {
            btn.onclick = (e) => {
                e.stopPropagation();
                btns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // Si se hizo clic en una opción del menú flyout
                if (btn.classList.contains('hud-dock-menu-btn')) {
                    if (dropdownLabel) {
                        const labelSpan = btn.querySelector('span:last-child');
                        dropdownLabel.textContent = labelSpan ? labelSpan.textContent.trim() : 'Zona';
                    }
                    if (dropdownToggle) dropdownToggle.classList.add('active');
                } else {
                    // Clic en Global o Bolivia/Chicago
                    if (dropdownLabel) dropdownLabel.textContent = activeContext === 'chicago' ? 'Distritos' : 'Ciudades';
                    if (dropdownToggle) dropdownToggle.classList.remove('active');
                }

                // Cerrar menú flyout
                if (dropdownMenu) {
                    dropdownMenu.classList.add('hidden');
                    if (dropdownChevron) dropdownChevron.style.transform = 'rotate(0deg)';
                }

                const targetKey = btn.dataset.city ? btn.dataset.city.toLowerCase() : (activeContext === 'chicago' ? 'chicago' : 'bolivia');
                const vp = VIEWPORTS[targetKey] || (activeContext === 'chicago' ? VIEWPORTS['chicago'] : VIEWPORTS['bolivia']);

                map.flyTo({
                    center: vp.center,
                    zoom: vp.zoom,
                    pitch: vp.pitch,
                    bearing: vp.bearing || 0,
                    duration: 2200,
                    curve: 1.42,
                    easing: (t) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
                    essential: true
                });
            };
        });
    }

    // Cerrar menú desplegable al hacer clic fuera
    document.addEventListener('click', (e) => {
        const dropdownMenu = document.getElementById('dock-dropdown-menu');
        const dropdownChevron = document.getElementById('dock-dropdown-chevron');
        if (dropdownMenu && !dropdownMenu.classList.contains('hidden')) {
            const wrapper = document.getElementById('dock-dropdown-wrapper');
            if (wrapper && !wrapper.contains(e.target)) {
                dropdownMenu.classList.add('hidden');
                if (dropdownChevron) dropdownChevron.style.transform = 'rotate(0deg)';
            }
        }
    });

    // Interceptar clics en los botones de cambio de contexto
    if (btnSwitchBolivia) {
        btnSwitchBolivia.addEventListener('click', (e) => {
            e.preventDefault();
            switchContext('bolivia');
        });
    }
    if (btnSwitchChicago) {
        btnSwitchChicago.addEventListener('click', (e) => {
            e.preventDefault();
            switchContext('chicago');
        });
    }

    bindCityButtons();

    // 6. Alternar Proyección 3D Globe ↔ 2D Plano Mercator
    if (btnToggleProj) {
        btnToggleProj.addEventListener('click', () => {
            isGlobeProjection = !isGlobeProjection;
            map.setProjection({ type: isGlobeProjection ? 'globe' : 'mercator' });

            const projIcon = document.getElementById('proj-icon');
            const projBadge = document.getElementById('proj-badge');

            if (projIcon) {
                projIcon.textContent = isGlobeProjection ? 'public' : 'map';
            }
            if (projBadge) {
                projBadge.innerHTML = isGlobeProjection
                    ? '<span class="size-1.5 rounded-full bg-cyan-400 inline-block mr-1"></span>3D GLOBO'
                    : '<span class="size-1.5 rounded-full bg-slate-400 inline-block mr-1"></span>2D PLANO';
            }

            if (isGlobeProjection) {
                btnToggleProj.classList.add('active');
            } else {
                btnToggleProj.classList.remove('active');
            }
        });
    }

    // 7. Alternar Agrupación WebGL (Clústeres con Números vs Puntos Individuales Continuos)
    if (btnToggleCluster) {
        btnToggleCluster.addEventListener('click', () => {
            setClusteringMode(!isClusteringEnabled);
        });
    }

    // 8. Filtros de categoría y centro urbano / distrito
    if (filterCategoryEl) {
        filterCategoryEl.addEventListener('change', loadGeojsonData);
    }
    if (filterCityEl) {
        filterCityEl.addEventListener('change', () => {
            loadGeojsonData();
            const selectedCity = filterCityEl.value.toLowerCase();
            if (VIEWPORTS[selectedCity]) {
                const vp = VIEWPORTS[selectedCity];
                map.flyTo({
                    center: vp.center,
                    zoom: vp.zoom,
                    pitch: vp.pitch,
                    bearing: vp.bearing || 0,
                    duration: 2000,
                    curve: 1.42,
                    easing: (t) => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
                    essential: true
                });
            }
        });
    }

    // 9. Modo Presentación / Cine (Repliegue y Restauración Suave de HUDs)
    const btnToggleCinema = document.getElementById('btn-toggle-cinema');
    const btnRestoreHud = document.getElementById('btn-restore-hud');

    function toggleCinemaMode() {
        if (!viewportEl) return;
        const isCinema = viewportEl.classList.toggle('cinema-mode');
        const cinemaBadge = document.getElementById('cinema-badge');
        const cinemaIcon = document.getElementById('cinema-icon');
        if (cinemaBadge) {
            cinemaBadge.innerHTML = isCinema
                ? '<span class="size-1.5 rounded-full bg-amber-400 inline-block mr-1"></span>ACTIVO'
                : '[H]';
        }
        if (cinemaIcon) {
            cinemaIcon.textContent = isCinema ? 'fullscreen_exit' : 'fullscreen';
        }
        if (btnToggleCinema) {
            btnToggleCinema.classList.toggle('active', isCinema);
        }
    }

    if (btnToggleCinema) {
        btnToggleCinema.addEventListener('click', toggleCinemaMode);
    }
    if (btnRestoreHud) {
        btnRestoreHud.addEventListener('click', toggleCinemaMode);
    }

    // Atajo de teclado táctico: [H] o [h] para alternar HUD limpio
    window.addEventListener('keydown', (e) => {
        const tag = (e.target && e.target.tagName) ? e.target.tagName.toLowerCase() : '';
        if (tag === 'input' || tag === 'select' || tag === 'textarea') return;

        if (e.key === 'h' || e.key === 'H') {
            e.preventDefault();
            toggleCinemaMode();
        }
    });

    // 10. Telemetría de Orientación y Cámara Orbital en Vivo
    const camAltEl = document.getElementById('cam-alt');
    const camPitchEl = document.getElementById('cam-pitch');
    const camBearingEl = document.getElementById('cam-bearing');
    const camZoomEl = document.getElementById('cam-zoom');

    function updateCameraTelemetry() {
        if (!map) return;
        const zoom = map.getZoom();
        const pitch = Math.round(map.getPitch());
        const rawBearing = (Math.round(map.getBearing()) + 360) % 360;

        // Altitud orbital aproximada desde el nivel de zoom
        const altKm = Math.round(40000 / Math.pow(2, zoom));
        const altStr = altKm > 999 ? `${(altKm / 1000).toFixed(1)}k km` : `${altKm} km`;

        const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
        const cardinal = directions[Math.round(rawBearing / 45) % 8];

        if (camAltEl) camAltEl.textContent = `ALT: ${altStr}`;
        if (camPitchEl) camPitchEl.innerHTML = `${pitch}&deg;`;
        if (camBearingEl) camBearingEl.innerHTML = `${rawBearing}&deg; ${cardinal}`;
        if (camZoomEl) camZoomEl.textContent = zoom.toFixed(1);
    }

    map.on('move', updateCameraTelemetry);
    map.on('rotate', updateCameraTelemetry);
    map.on('pitch', updateCameraTelemetry);

    // 11. Plegado / Desplegado Táctico de HUDs (Leyenda y Toolbar)
    const legendHeaderToggle = document.getElementById('legend-header-toggle');
    const hudLegendCard = document.getElementById('hud-legend-card');
    if (legendHeaderToggle && hudLegendCard) {
        legendHeaderToggle.addEventListener('click', () => {
            hudLegendCard.classList.toggle('collapsed');
        });
    }

    const toolbarHeaderToggle = document.getElementById('toolbar-header-toggle');
    const hudTopRight = document.getElementById('hud-top-right');
    if (toolbarHeaderToggle && hudTopRight) {
        toolbarHeaderToggle.addEventListener('click', () => {
            hudTopRight.classList.toggle('collapsed');
        });
    }

    // Inicialización de estado y telemetría
    if (viewportEl) {
        viewportEl.setAttribute('data-algo-theme', currentClusterMode);
    }
    updateCameraTelemetry();
});
