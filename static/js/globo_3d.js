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
    const bottomControlsEl = document.querySelector('.hud-bottom-controls');
    const btnSwitchBolivia = document.getElementById('btn-switch-bolivia');
    const btnSwitchChicago = document.getElementById('btn-switch-chicago');

    // Selectores del Modo Algorítmico (Delito / DBSCAN / OPTICS / GMM / Ward)
    const btnModeCategory = document.getElementById('btn-mode-category');
    const btnModeDbscan = document.getElementById('btn-mode-dbscan');
    const btnModeOptics = document.getElementById('btn-mode-optics');
    const btnModeGmm = document.getElementById('btn-mode-gmm');
    const btnModeWard = document.getElementById('btn-mode-ward');
    const activeModeLabel = document.getElementById('active-mode-label');

    // Secciones de Leyenda
    const legendCategory = document.getElementById('legend-category-section');
    const legendDbscan = document.getElementById('legend-dbscan-section');
    const legendOptics = document.getElementById('legend-optics-section');
    const legendGmm = document.getElementById('legend-gmm-section');
    const legendWard = document.getElementById('legend-ward-section');

    let currentClusterMode = 'category';

    // Centros urbanos y distritos policiales predefinidos
    const VIEWPORTS = {
        'global': { center: [0, 20], zoom: 1.8, pitch: 0, bearing: 0 },
        // Bolivia (Primario)
        'bolivia': { center: [-64.9, -16.5], zoom: 5.0, pitch: 25, bearing: 0 },
        'santa cruz': { center: [-63.1821, -17.7833], zoom: 12.5, pitch: 45, bearing: -15 },
        'la paz': { center: [-68.1336, -16.4958], zoom: 13.0, pitch: 45, bearing: 20 },
        'el alto': { center: [-68.1630, -16.5075], zoom: 13.0, pitch: 40, bearing: 10 },
        'cochabamba': { center: [-66.1570, -17.3935], zoom: 12.8, pitch: 40, bearing: 0 },
        'viacha': { center: [-68.3000, -16.6533], zoom: 14.0, pitch: 45, bearing: 0 },
        'riberalta': { center: [-66.0631, -11.0042], zoom: 13.5, pitch: 35, bearing: 0 },
        'punata': { center: [-65.8333, -17.5500], zoom: 14.0, pitch: 40, bearing: 0 },
        'warnes': { center: [-63.1667, -17.5167], zoom: 13.5, pitch: 35, bearing: 0 },
        // Chicago (Benchmark Secundario)
        'chicago': { center: [-87.6298, 41.8781], zoom: 10.5, pitch: 35, bearing: -10 },
        'the loop': { center: [-87.6231, 41.8818], zoom: 13.5, pitch: 45, bearing: -15 },
        'west side': { center: [-87.7200, 41.8750], zoom: 13.0, pitch: 40, bearing: 0 },
        'south side': { center: [-87.6400, 41.7750], zoom: 13.0, pitch: 40, bearing: 0 },
        'north side': { center: [-87.6500, 41.9400], zoom: 13.0, pitch: 40, bearing: 0 }
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

    // 2. Evento Load: Atmósfera Estelar y Capas
    map.on('load', () => {
        if (typeof map.setSky === 'function') {
            map.setSky({
                'sky-color': '#030712',
                'sky-horizon-blend': 0.6,
                'horizon-color': '#0e1726',
                'horizon-fog-blend': 0.8,
                'fog-color': '#030712',
                'fog-ground-blend': 0.5
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
                } else {
                    setupGeojsonLayers(data);
                }
            })
            .catch(err => console.error("[WebGIS] Error cargando GeoJSON:", err));
    }

    // 4. Capas Vectoriales de Clustering WebGL
    function setupGeojsonLayers(geojson) {
        map.addSource('webgis-events', {
            type: 'geojson',
            data: geojson,
            cluster: true,
            clusterMaxZoom: 14,
            clusterRadius: 50
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

        // Marcadores individuales con paleta unificada para Bolivia y Chicago
        map.addLayer({
            id: 'unclustered-point',
            type: 'circle',
            source: 'webgis-events',
            filter: ['!', ['has', 'point_count']],
            paint: {
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

        // Aplicar estilo de color según el modo algorítmico activo
        applyClusterStyle(currentClusterMode);

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

        // Clic en incidente individual: Popup táctico enriquecido con DBSCAN, OPTICS y GMM
        map.on('click', 'unclustered-point', (e) => {
            const feature = e.features[0];
            const coords = feature.geometry.coordinates.slice();
            const props = feature.properties;

            while (Math.abs(e.lngLat.lng - coords[0]) > 180) {
                coords[0] += e.lngLat.lng > coords[0] ? 360 : -360;
            }

            const dbscanBadgeClass = (props.dbscan === -1 || props.dbscan === '-1')
                ? 'bg-slate-700/60 text-slate-300 border-slate-600'
                : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';

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
                        
                        <!-- Badges No Supervisados: DBSCAN, OPTICS, GMM & Ward -->
                        <div class="pt-2 mt-1 border-t border-outline-variant/60 flex flex-col gap-1">
                            <div class="flex items-center gap-1.5">
                                <span class="px-1.5 py-0.5 rounded text-[10px] font-bold border ${dbscanBadgeClass}">
                                    ${props.dbscan_label || ('DBSCAN: Hotspot #' + props.dbscan)}
                                </span>
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
        });

        map.on('mouseenter', 'clusters-core', () => map.getCanvas().style.cursor = 'pointer');
        map.on('mouseleave', 'clusters-core', () => map.getCanvas().style.cursor = '');
        map.on('mouseenter', 'unclustered-point', () => map.getCanvas().style.cursor = 'pointer');
        map.on('mouseleave', 'unclustered-point', () => map.getCanvas().style.cursor = '');
    }

    // 5. Aplicar Estilos de Shaders Dinámicos (Categoría vs DBSCAN vs OPTICS vs GMM)
    function applyClusterStyle(mode) {
        if (!map || !map.getLayer('unclustered-point')) return;

        if (mode === 'category') {
            map.setPaintProperty('unclustered-point', 'circle-color', [
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
            map.setPaintProperty('unclustered-point', 'circle-opacity', 1.0);
            map.setPaintProperty('unclustered-point', 'circle-stroke-color', '#ffffff');
            map.setPaintProperty('unclustered-point', 'circle-stroke-width', 2);

        } else if (mode === 'dbscan') {
            if (activeContext === 'chicago') {
                map.setPaintProperty('unclustered-point', 'circle-color', [
                    'match',
                    ['get', 'dbscan'],
                    1, '#00e5ff',
                    2, '#ff3366',
                    3, '#ffaa00',
                    4, '#a855f7',
                    /* Ruido */ '#64748b'
                ]);
            } else {
                map.setPaintProperty('unclustered-point', 'circle-color', [
                    'match',
                    ['get', 'dbscan'],
                    0, '#00e5ff',
                    1, '#34d399',
                    2, '#ff3366',
                    3, '#fbbf24',
                    4, '#10b981',
                    5, '#818cf8',
                    /* Ruido */ '#64748b'
                ]);
            }

            map.setPaintProperty('unclustered-point', 'circle-opacity', [
                'case',
                ['==', ['get', 'dbscan'], -1], 0.40,
                0.95
            ]);
            map.setPaintProperty('unclustered-point', 'circle-stroke-color', [
                'case',
                ['==', ['get', 'dbscan'], -1], '#475569',
                '#ffffff'
            ]);
            map.setPaintProperty('unclustered-point', 'circle-stroke-width', 1.8);

        } else if (mode === 'optics') {
            if (activeContext === 'chicago') {
                map.setPaintProperty('unclustered-point', 'circle-color', [
                    'match',
                    ['get', 'optics'],
                    1, '#00e5ff',
                    2, '#ff3366',
                    3, '#ffaa00',
                    4, '#a855f7',
                    /* Ruido */ '#64748b'
                ]);
            } else {
                map.setPaintProperty('unclustered-point', 'circle-color', [
                    'match',
                    ['get', 'optics'],
                    0, '#00e5ff',
                    1, '#38bdf8',
                    2, '#ff3366',
                    3, '#f43f5e',
                    4, '#10b981',
                    5, '#818cf8',
                    6, '#34d399',
                    7, '#34d399',
                    /* Ruido */ '#64748b'
                ]);
            }

            map.setPaintProperty('unclustered-point', 'circle-opacity', [
                'case',
                ['==', ['get', 'optics'], -1], 0.35,
                0.95
            ]);
            map.setPaintProperty('unclustered-point', 'circle-stroke-color', [
                'case',
                ['==', ['get', 'optics'], -1], '#334155',
                '#ffffff'
            ]);
            map.setPaintProperty('unclustered-point', 'circle-stroke-width', 2);

        } else if (mode === 'gmm') {
            // Modo 4: Componentes Gaussianas y Elipses Multivariantes GMM
            if (activeContext === 'chicago') {
                map.setPaintProperty('unclustered-point', 'circle-color', [
                    'match',
                    ['get', 'gmm'],
                    1, '#00e5ff',
                    2, '#ff3366',
                    3, '#ffaa00',
                    /* Dispersión */ '#64748b'
                ]);
            } else {
                map.setPaintProperty('unclustered-point', 'circle-color', [
                    'match',
                    ['get', 'gmm'],
                    0, '#00e5ff',
                    1, '#ff3366',
                    2, '#34d399',
                    3, '#818cf8',
                    /* Dispersión */ '#64748b'
                ]);
            }

            map.setPaintProperty('unclustered-point', 'circle-opacity', [
                'case',
                ['==', ['get', 'gmm'], -1], 0.35,
                0.92
            ]);
            map.setPaintProperty('unclustered-point', 'circle-stroke-color', [
                'case',
                ['==', ['get', 'gmm'], -1], '#334155',
                '#ffffff'
            ]);
            map.setPaintProperty('unclustered-point', 'circle-stroke-width', 2);

        } else if (mode === 'ward') {
            // Modo 5: Macro-Clusters Jerárquicos Aglomerativos (Ward Linkage k=3)
            if (activeContext === 'chicago') {
                map.setPaintProperty('unclustered-point', 'circle-color', [
                    'match',
                    ['get', 'ward_macro'],
                    'A', '#ff3366',
                    'B', '#00e5ff',
                    'C', '#34d399',
                    /* Fallback */ '#94a3b8'
                ]);
            } else {
                map.setPaintProperty('unclustered-point', 'circle-color', [
                    'match',
                    ['get', 'ward_macro'],
                    'A', '#ff3366',
                    'B', '#fbbf24',
                    'C', '#34d399',
                    /* Fallback */ '#94a3b8'
                ]);
            }

            map.setPaintProperty('unclustered-point', 'circle-opacity', 0.95);
            map.setPaintProperty('unclustered-point', 'circle-stroke-color', '#ffffff');
            map.setPaintProperty('unclustered-point', 'circle-stroke-width', 2);
        }
    }

    // 6. Conmutación de Modo Algorítmico (Delito / DBSCAN / OPTICS / GMM / Ward)
    function setClusterMode(newMode) {
        currentClusterMode = newMode;

        [btnModeCategory, btnModeDbscan, btnModeOptics, btnModeGmm, btnModeWard].forEach(b => {
            if (b) b.classList.remove('active');
        });

        if (newMode === 'category' && btnModeCategory) btnModeCategory.classList.add('active');
        if (newMode === 'dbscan' && btnModeDbscan) btnModeDbscan.classList.add('active');
        if (newMode === 'optics' && btnModeOptics) btnModeOptics.classList.add('active');
        if (newMode === 'gmm' && btnModeGmm) btnModeGmm.classList.add('active');
        if (newMode === 'ward' && btnModeWard) btnModeWard.classList.add('active');

        if (activeModeLabel) {
            activeModeLabel.textContent = newMode === 'category' ? 'DELITOS' : newMode.toUpperCase();
            if (newMode === 'category') activeModeLabel.className = 'text-primary-container font-semibold';
            else if (newMode === 'dbscan') activeModeLabel.className = 'text-cyan-400 font-bold';
            else if (newMode === 'optics') activeModeLabel.className = 'text-amber-400 font-bold';
            else if (newMode === 'gmm') activeModeLabel.className = 'text-emerald-400 font-bold';
            else if (newMode === 'ward') activeModeLabel.className = 'text-purple-400 font-bold';
        }

        if (legendCategory) legendCategory.classList.toggle('hidden', newMode !== 'category');
        if (legendDbscan) legendDbscan.classList.toggle('hidden', newMode !== 'dbscan');
        if (legendOptics) legendOptics.classList.toggle('hidden', newMode !== 'optics');
        if (legendGmm) legendGmm.classList.toggle('hidden', newMode !== 'gmm');
        if (legendWard) legendWard.classList.toggle('hidden', newMode !== 'ward');

        applyClusterStyle(newMode);
    }

    if (btnModeCategory) btnModeCategory.addEventListener('click', () => setClusterMode('category'));
    if (btnModeDbscan) btnModeDbscan.addEventListener('click', () => setClusterMode('dbscan'));
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

        // Vuelo suave de cámara al centroide del contexto seleccionado
        const vp = newCtx === 'chicago' ? VIEWPORTS['chicago'] : VIEWPORTS['bolivia'];
        map.flyTo({
            center: vp.center,
            zoom: vp.zoom,
            pitch: vp.pitch,
            bearing: vp.bearing || 0,
            duration: 2000,
            essential: true
        });

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
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn active" data-city="chicago" title="Metro Chicago">
                    <span class="material-symbols-outlined text-sm">location_city</span>
                    <span>Chicago</span>
                </button>
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn" data-city="the loop" title="Distrito 1 - The Loop">
                    <span class="material-symbols-outlined text-sm">domain</span>
                    <span>The Loop</span>
                </button>
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn" data-city="west side" title="Distrito 11 - West Side">
                    <span class="material-symbols-outlined text-sm">warning</span>
                    <span>West Side</span>
                </button>
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn" data-city="south side" title="Distrito 7 - South Side">
                    <span class="material-symbols-outlined text-sm">near_me</span>
                    <span>South Side</span>
                </button>
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn" data-city="north side" title="Distrito 19 - North Side">
                    <span class="material-symbols-outlined text-sm">shield</span>
                    <span>North Side</span>
                </button>
            `;
        } else {
            bottomControlsEl.innerHTML = `
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn" data-city="global" title="Vista Planeta Completo">
                    <span class="material-symbols-outlined text-sm">public</span>
                    <span>Global</span>
                </button>
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn active" data-city="bolivia" title="Enfoque Nacional Bolivia">
                    <span class="material-symbols-outlined text-sm">flag</span>
                    <span>Bolivia</span>
                </button>
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn" data-city="santa cruz" title="Área Metropolitana Santa Cruz">
                    <span class="material-symbols-outlined text-sm">apartment</span>
                    <span>Santa Cruz</span>
                </button>
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn" data-city="la paz" title="Sede de Gobierno La Paz">
                    <span class="material-symbols-outlined text-sm">terrain</span>
                    <span>La Paz</span>
                </button>
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn" data-city="el alto" title="Área Metropolitana El Alto">
                    <span class="material-symbols-outlined text-sm">altitude</span>
                    <span>El Alto</span>
                </button>
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn" data-city="cochabamba" title="Valle Central de Cochabamba">
                    <span class="material-symbols-outlined text-sm">location_on</span>
                    <span>Cochabamba</span>
                </button>
                <button type="button" class="btn-tactile hud-dock-btn hud-city-btn" data-city="viacha" title="Municipio de Viacha (Lugar del Hecho)">
                    <span class="material-symbols-outlined text-sm">explore</span>
                    <span>Viacha</span>
                </button>
            `;
        }
        bindCityButtons();
    }

    // Enlazar clics de botones del dock inferior
    function bindCityButtons() {
        const btns = document.querySelectorAll('.hud-city-btn');
        btns.forEach(btn => {
            btn.addEventListener('click', () => {
                btns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const targetKey = btn.dataset.city ? btn.dataset.city.toLowerCase() : (activeContext === 'chicago' ? 'chicago' : 'bolivia');
                const vp = VIEWPORTS[targetKey] || (activeContext === 'chicago' ? VIEWPORTS['chicago'] : VIEWPORTS['bolivia']);

                map.flyTo({
                    center: vp.center,
                    zoom: vp.zoom,
                    pitch: vp.pitch,
                    bearing: vp.bearing || 0,
                    duration: 1800,
                    essential: true
                });
            });
        });
    }

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
                projBadge.textContent = isGlobeProjection ? '3D GLOBO' : '2D PLANO';
            }

            if (isGlobeProjection) {
                btnToggleProj.classList.add('active');
            } else {
                btnToggleProj.classList.remove('active');
            }
        });
    }

    // 7. Filtros de categoría y centro urbano / distrito
    if (filterCategoryEl) {
        filterCategoryEl.addEventListener('change', loadGeojsonData);
    }
    if (filterCityEl) {
        filterCityEl.addEventListener('change', () => {
            loadGeojsonData();
            const selectedCity = filterCityEl.value.toLowerCase();
            if (VIEWPORTS[selectedCity]) {
                const vp = VIEWPORTS[selectedCity];
                map.flyTo({ center: vp.center, zoom: vp.zoom, pitch: vp.pitch, duration: 1500 });
            }
        });
    }
});
