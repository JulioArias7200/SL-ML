/**
 * GLOBO 3D WEBGIS // PLATAFORMA DE INTELIGENCIA URBANA
 * MapLibre GL JS v4+ con soporte de Globo Esférico, Clustering WebGL y Teselas Vectoriales
 */

document.addEventListener('DOMContentLoaded', () => {
    let map;
    let isGlobeProjection = true;
    let currentGeojson = null;

    // Elementos del DOM
    const statTotalEl = document.getElementById('stat-total-events');
    const filterCategoryEl = document.getElementById('filter-category');
    const filterCityEl = document.getElementById('filter-city');
    const btnToggleProj = document.getElementById('btn-toggle-projection');
    const cityButtons = document.querySelectorAll('.hud-city-btn');

    // Centros urbanos predefinidos
    const VIEWPORTS = {
        'global': { center: [0, 20], zoom: 1.8, pitch: 0, bearing: 0 },
        'bolivia': { center: [-64.9, -16.5], zoom: 5.4, pitch: 25, bearing: 0 },
        'santa cruz': { center: [-63.1821, -17.7833], zoom: 12.5, pitch: 45, bearing: -15 },
        'la paz': { center: [-68.1336, -16.4958], zoom: 13.0, pitch: 45, bearing: 20 },
        'cochabamba': { center: [-66.1570, -17.3935], zoom: 12.8, pitch: 40, bearing: 0 }
    };

    // 1. Inicializar Mapa con Proyección Globe 3D
    map = new maplibregl.Map({
        container: 'map-container',
        // Teselas vectoriales libres de OpenFreeMap (estilo Liberty)
        style: 'https://tiles.openfreemap.org/styles/liberty',
        center: [-64.9, -16.5],
        zoom: 4.8,
        minZoom: 1.5,
        maxZoom: 18,
        projection: {
            type: 'globe' // Proyección 3D esférica en MapLibre v4
        }
    });

    // Controles de navegación y escala táctica
    map.addControl(new maplibregl.NavigationControl({
        visualizePitch: true,
        showCompass: true
    }), 'bottom-right');

    map.addControl(new maplibregl.ScaleControl({
        maxWidth: 120,
        unit: 'metric'
    }), 'bottom-left');

    // 2. Evento Load: Configuración de Atmósfera, Capas y Fuentes
    map.on('load', () => {
        // Cielo y horizonte estelar (efecto de espacio exterior)
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

        // Cargar datos GeoJSON desde el backend Flask
        loadGeojsonData();
    });

    // 3. Función para cargar y actualizar la fuente GeoJSON
    function loadGeojsonData() {
        const cat = filterCategoryEl ? filterCategoryEl.value : 'todos';
        const city = filterCityEl ? filterCityEl.value : 'todas';

        let url = `/api/v1/webgis/geojson?categoria=${encodeURIComponent(cat)}&ciudad=${encodeURIComponent(city)}`;

        fetch(url)
            .then(res => res.json())
            .then(data => {
                currentGeojson = data;
                
                if (statTotalEl) {
                    statTotalEl.textContent = data.total || 0;
                }

                if (map.getSource('bolivia-news')) {
                    map.getSource('bolivia-news').setData(data);
                } else {
                    setupGeojsonLayers(data);
                }
            })
            .catch(err => console.error("[WebGIS] Error cargando GeoJSON:", err));
    }

    // 4. Configuración de capas vectoriales de Clustering WebGL
    function setupGeojsonLayers(geojson) {
        map.addSource('bolivia-news', {
            type: 'geojson',
            data: geojson,
            cluster: true,
            clusterMaxZoom: 14, // A partir de zoom 15 se muestran puntos individuales
            clusterRadius: 50
        });

        // Capa A: Halo exterior concéntrico de clusters
        map.addLayer({
            id: 'clusters-halo',
            type: 'circle',
            source: 'bolivia-news',
            filter: ['has', 'point_count'],
            paint: {
                'circle-color': [
                    'step',
                    ['get', 'point_count'],
                    'rgba(0, 229, 255, 0.25)',   // < 5 incidentes: Cyan
                    5, 'rgba(251, 191, 36, 0.25)', // 5 a 15: Ámbar
                    15, 'rgba(255, 51, 102, 0.3)' // > 15: Alerta Roja
                ],
                'circle-radius': [
                    'step',
                    ['get', 'point_count'],
                    22,
                    5, 30,
                    15, 40
                ],
                'circle-blur': 0.2
            }
        });

        // Capa B: Núcleo interior sólido
        map.addLayer({
            id: 'clusters-core',
            type: 'circle',
            source: 'bolivia-news',
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

        // Capa C: Conteo numérico de incidentes
        map.addLayer({
            id: 'cluster-count',
            type: 'symbol',
            source: 'bolivia-news',
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

        // Capa D: Marcadores individuales de incidentes
        map.addLayer({
            id: 'unclustered-point',
            type: 'circle',
            source: 'bolivia-news',
            filter: ['!', ['has', 'point_count']],
            paint: {
                'circle-color': [
                    'match',
                    ['get', 'category'],
                    'Robo Agravado / Asalto', '#ff3366',
                    'Agresión Física y Lesiones', '#fbbf24',
                    'Hurto / Descuidismo', '#00e5ff',
                    'Homicidio / Asesinato', '#ff0033',
                    'Narcotráfico / Drogas', '#34d399',
                    /* default */ '#38bdf8'
                ],
                'circle-radius': 7,
                'circle-stroke-width': 2,
                'circle-stroke-color': '#ffffff'
            }
        });

        // 5. Interacción de Clic en Clusters: Expansión suave con easeTo
        map.on('click', 'clusters-core', (e) => {
            const features = map.queryRenderedFeatures(e.point, { layers: ['clusters-core'] });
            if (!features.length) return;

            const clusterId = features[0].properties.cluster_id;
            map.getSource('bolivia-news').getClusterExpansionZoom(clusterId, (err, zoom) => {
                if (err) return;

                map.easeTo({
                    center: features[0].geometry.coordinates,
                    zoom: zoom + 0.8,
                    pitch: Math.min(50, map.getPitch() + 15),
                    duration: 1000
                });
            });
        });

        // 6. Interacción de Clic en Marcador Individual: Popup Táctico
        map.on('click', 'unclustered-point', (e) => {
            const feature = e.features[0];
            const coords = feature.geometry.coordinates.slice();
            const props = feature.properties;

            // Prevenir desfases en envolturas de proyección
            while (Math.abs(e.lngLat.lng - coords[0]) > 180) {
                coords[0] += e.lngLat.lng > coords[0] ? 360 : -360;
            }

            const popupContent = `
                <div class="news-popup-container">
                    <span class="news-popup-category">${props.category || 'Incidente'}</span>
                    <h4 class="news-popup-title">${props.title}</h4>
                    <div class="news-popup-meta">
                        <div><span>📍 Zona:</span> <strong>${props.zone || props.city}</strong></div>
                        <div><span>📅 Fecha:</span> <strong>${props.date}</strong></div>
                        <div><span>🏛️ Ciudad:</span> <strong>${props.city}</strong></div>
                        <div><span>📰 Fuente:</span> <strong>${props.source}</strong></div>
                    </div>
                    ${props.url && props.url !== '#' ? `
                        <a href="${props.url}" target="_blank" rel="noopener noreferrer" class="news-popup-link">
                            <span>Ver Noticia Completa</span>
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

        // Cursores al pasar el ratón
        map.on('mouseenter', 'clusters-core', () => map.getCanvas().style.cursor = 'pointer');
        map.on('mouseleave', 'clusters-core', () => map.getCanvas().style.cursor = '');
        map.on('mouseenter', 'unclustered-point', () => map.getCanvas().style.cursor = 'pointer');
        map.on('mouseleave', 'unclustered-point', () => map.getCanvas().style.cursor = '');
    }

    // 7. Eventos de Controles y Botones HUD

    // Botones de salto a ciudades
    cityButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            cityButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const targetKey = btn.dataset.city ? btn.dataset.city.toLowerCase() : 'bolivia';
            const vp = VIEWPORTS[targetKey] || VIEWPORTS['bolivia'];

            map.flyTo({
                center: vp.center,
                zoom: vp.zoom,
                pitch: vp.pitch,
                bearing: vp.bearing,
                duration: 1800,
                essential: true
            });
        });
    });

    // Conmutador de Proyección 3D Globe ↔ 2D Mercator
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

    // Filtros de categoría y ciudad
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

