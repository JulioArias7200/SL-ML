/**
 * CPD & BOLIVIA ANALYTICS CORE // SPATIAL & OPTICS DENSITY CONTROLS
 * Control de sliders Haversine y OPTICS (Xi-gradient), conmutador de capas multiescala,
 * brushing & linking interactivo entre Reachability Plot, Mapa Táctico y Tabla.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Detección de Contexto Activo (Bolivia vs Chicago)
    const spatialRoot = document.getElementById('spatial-root');
    const currentCtx = (spatialRoot && spatialRoot.getAttribute('data-context')) 
        ? spatialRoot.getAttribute('data-context').toLowerCase() 
        : 'bolivia';

    // 2. Elementos DOM de Haversine HUD
    const epsSlider = document.getElementById('slider-eps');
    const minPtsSlider = document.getElementById('slider-min-pts');
    const epsValDisplay = document.getElementById('val-eps-display');
    const minPtsValDisplay = document.getElementById('val-min-pts-display');
    const hotspotsCountDisplay = document.getElementById('val-hotspots-count');
    const noiseCountDisplay = document.getElementById('val-noise-count');

    // 3. Elementos DOM de OPTICS Controls
    const xiSlider = document.getElementById('slider-xi');
    const xiValDisplay = document.getElementById('val-xi-display');
    const opticsThresholdVal = document.getElementById('optics-threshold-val');
    const opticsValleysCount = document.getElementById('optics-valleys-count');
    const opticsNoiseCount = document.getElementById('optics-noise-count');
    const btnMethodXi = document.getElementById('btn-optics-method-xi');
    const btnMethodEps = document.getElementById('btn-optics-method-eps');
    let currentOpticsMethod = 'xi';

    // SVG Reachability Elements
    const thresholdLine = document.getElementById('optics-threshold-line');
    const thresholdBadge = document.getElementById('optics-threshold-badge');
    const thresholdText = document.getElementById('optics-threshold-text');
    const opticsBarsGroup = document.getElementById('optics-bars-group');
    const opticsTooltip = document.getElementById('optics-tooltip');
    const tooltipPointId = document.getElementById('tooltip-point-id');
    const tooltipClusterBadge = document.getElementById('tooltip-cluster-badge');
    const tooltipZoneName = document.getElementById('tooltip-zone-name');
    const tooltipSubName = document.getElementById('tooltip-sub-name');
    const tooltipReachDist = document.getElementById('tooltip-reach-dist');

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

    // 4. Actualización de Parámetros Haversine (DBSCAN)
    async function updateSpatialParams() {
        if (!epsSlider || !minPtsSlider) return;
        const eps = parseInt(epsSlider.value);
        const minPts = parseInt(minPtsSlider.value);

        if (epsValDisplay) {
            const epsRad = (eps / 6371008.8).toFixed(6);
            epsValDisplay.textContent = `${eps} m (${epsRad} rad)`;
        }

        if (minPtsValDisplay) {
            minPtsValDisplay.textContent = `${minPts} pts`;
        }

        try {
            const res = await fetch(`/api/v1/spatial_filter?ctx=${currentCtx}&eps=${eps}&min_pts=${minPts}`);
            const data = await res.json();
            if (data.active_hotspots && hotspotsCountDisplay) {
                hotspotsCountDisplay.textContent = `${data.active_hotspots} ZONAS`;
            }
            if (data.noise_count && noiseCountDisplay) {
                noiseCountDisplay.textContent = `Ruido: ${data.noise_count} pts`;
            }
        } catch (e) {
            console.error("Error al actualizar parámetros Haversine:", e);
        }
    }

    if (epsSlider) epsSlider.addEventListener('input', updateSpatialParams);
    if (minPtsSlider) minPtsSlider.addEventListener('input', updateSpatialParams);

    // 5. Actualización Dinámica del Algoritmo OPTICS (Xi Gradient & Reachability Threshold)
    async function updateOpticsParams() {
        if (!xiSlider) return;
        const xiVal = parseFloat(xiSlider.value);

        if (xiValDisplay) {
            xiValDisplay.textContent = `ξ = ${xiVal.toFixed(2)}`;
        }

        try {
            const res = await fetch(`/api/v1/optics_data?ctx=${currentCtx}&xi=${xiVal}&method=${currentOpticsMethod}`);
            const data = await res.json();
            if (!data || !data.reachability_points) return;

            // Actualizar contadores
            if (opticsThresholdVal) {
                opticsThresholdVal.textContent = `${data.threshold_m.toLocaleString()} m`;
            }
            if (opticsValleysCount) {
                opticsValleysCount.textContent = `${data.active_valleys_count} Activos`;
            }
            if (opticsNoiseCount) {
                opticsNoiseCount.textContent = `${data.noise_count} (${data.noise_pct}%)`;
            }

            // Reposicionar Línea de Umbral SVG
            const maxScale = data.max_reach_scale || (currentCtx === 'chicago' ? 520 : 3600);
            let thY = 215 - (data.threshold_m / maxScale * 165);
            if (thY < 20) thY = 20;
            if (thY > 215) thY = 215;

            if (thresholdLine) {
                thresholdLine.setAttribute('y1', thY.toFixed(1));
                thresholdLine.setAttribute('y2', thY.toFixed(1));
            }
            if (thresholdBadge) {
                thresholdBadge.setAttribute('y', (thY - 18).toFixed(1));
            }
            if (thresholdText) {
                thresholdText.setAttribute('y', (thY - 6).toFixed(1));
                thresholdText.textContent = `UMBRAL ξ CUT: ${data.threshold_m.toLocaleString()} m`;
            }

            // Actualizar Barras del Reachability Plot en vivo
            const bars = document.querySelectorAll('.optics-bar');
            data.reachability_points.forEach((pt, idx) => {
                const bar = bars[idx];
                if (bar) {
                    bar.setAttribute('fill', pt.color);
                    bar.setAttribute('opacity', pt.is_noise ? '0.40' : '0.90');
                    bar.setAttribute('data-noise', pt.is_noise ? 'true' : 'false');
                    bar.setAttribute('data-cluster', pt.cluster_id);
                }
            });

        } catch (e) {
            console.error("Error al actualizar OPTICS:", e);
        }
    }

    if (xiSlider) xiSlider.addEventListener('input', updateOpticsParams);

    // Toggle de Métodos de Extracción OPTICS
    if (btnMethodXi && btnMethodEps) {
        btnMethodXi.addEventListener('click', () => {
            currentOpticsMethod = 'xi';
            btnMethodXi.className = "flex-1 py-1 px-2.5 rounded bg-amber-400/20 border border-amber-400/50 text-amber-300 text-[11px] font-bold text-center transition-colors";
            btnMethodEps.className = "flex-1 py-1 px-2.5 rounded bg-surface-container border border-outline-variant text-outline hover:text-on-surface text-[11px] text-center transition-colors";
            updateOpticsParams();
        });

        btnMethodEps.addEventListener('click', () => {
            currentOpticsMethod = 'epsilon';
            btnMethodEps.className = "flex-1 py-1 px-2.5 rounded bg-cyan-400/20 border border-cyan-400/50 text-cyan-300 text-[11px] font-bold text-center transition-colors";
            btnMethodXi.className = "flex-1 py-1 px-2.5 rounded bg-surface-container border border-outline-variant text-outline hover:text-on-surface text-[11px] text-center transition-colors";
            updateOpticsParams();
        });
    }

    // 6. Conmutador de Capas Cartográficas Tácticas (DBSCAN / OPTICS / Ruido / KDE)
    const layerButtons = document.querySelectorAll('[data-layer-toggle]');
    layerButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const layerType = btn.getAttribute('data-layer-toggle');
            const icon = btn.querySelector('.material-symbols-outlined');
            const isActive = btn.classList.contains('active-layer');

            if (isActive) {
                btn.classList.remove('active-layer', 'bg-primary-container', 'bg-amber-500/20', 'bg-emerald-500/20', 'bg-rose-500/20', 'border-emerald-500/50', 'border-amber-500/50', 'border-rose-500/50', 'text-on-primary', 'text-amber-300', 'text-emerald-300', 'text-rose-300', 'font-bold');
                btn.classList.add('bg-surface-container', 'text-on-surface-variant', 'border-outline-variant');
                if (icon) icon.textContent = 'check_box_outline_blank';
                setLayerVisibility(layerType, false);
            } else {
                btn.classList.add('active-layer', 'font-bold');
                btn.classList.remove('bg-surface-container', 'text-on-surface-variant', 'border-outline-variant');
                if (layerType === 'optics') {
                    btn.classList.add('bg-amber-500/20', 'border', 'border-amber-500/50', 'text-amber-300');
                } else if (layerType === 'hdbscan') {
                    btn.classList.add('bg-emerald-500/20', 'border', 'border-emerald-500/50', 'text-emerald-300');
                } else if (layerType === 'kde') {
                    btn.classList.add('bg-rose-500/20', 'border', 'border-rose-500/50', 'text-rose-300');
                } else {
                    btn.classList.add('bg-primary-container', 'text-on-primary');
                }
                if (icon) icon.textContent = 'check_box';
                setLayerVisibility(layerType, true);
            }
        });
    });

    function setLayerVisibility(type, visible) {
        const opacity = visible ? '1' : '0';
        const pointer = visible ? 'auto' : 'none';

        if (type === 'optics') {
            const opticsLayer = document.querySelector('.optics-multiscale-layer');
            if (opticsLayer) {
                opticsLayer.style.opacity = opacity;
                opticsLayer.setAttribute('opacity', opacity);
                opticsLayer.style.pointerEvents = pointer;
            }
        } else if (type === 'hdbscan') {
            const hdbscanLayer = document.getElementById(currentCtx === 'chicago' ? 'layer-hdbscan-chicago' : 'layer-hdbscan-bolivia');
            if (hdbscanLayer) {
                hdbscanLayer.style.opacity = opacity;
                hdbscanLayer.setAttribute('opacity', opacity);
            }
        } else if (type === 'dbscan') {
            const dbscanLayer = document.getElementById(currentCtx === 'chicago' ? 'layer-dbscan-chicago' : 'layer-dbscan-bolivia');
            if (dbscanLayer) {
                dbscanLayer.style.opacity = opacity;
                dbscanLayer.setAttribute('opacity', opacity);
            }
        } else if (type === 'noise') {
            const noiseLayer = document.getElementById(currentCtx === 'chicago' ? 'layer-noise-chicago' : 'layer-noise-bolivia');
            if (noiseLayer) {
                noiseLayer.style.opacity = opacity;
                noiseLayer.setAttribute('opacity', opacity);
            }
        } else if (type === 'kde') {
            const kdeLayer = document.getElementById(currentCtx === 'chicago' ? 'layer-kde-chicago' : 'layer-kde-bolivia');
            if (kdeLayer) {
                if (visible) {
                    kdeLayer.style.display = 'inline';
                    requestAnimationFrame(() => {
                        kdeLayer.style.opacity = '1';
                        kdeLayer.setAttribute('opacity', '1');
                    });
                } else {
                    kdeLayer.style.opacity = '0';
                    kdeLayer.setAttribute('opacity', '0');
                    setTimeout(() => {
                        if (kdeLayer.getAttribute('opacity') === '0') {
                            kdeLayer.style.display = 'none';
                        }
                    }, 500);
                }
            }
            const kdeLegend = document.getElementById('legend-kde-indicator');
            if (kdeLegend) {
                kdeLegend.style.display = visible ? 'flex' : 'none';
            }
        }
    }

    // 7. Interacción de Brushing & Linking y Tooltips en el Reachability Plot
    const bars = document.querySelectorAll('.optics-bar');
    bars.forEach(bar => {
        bar.addEventListener('mouseenter', () => {
            bar.setAttribute('stroke', '#ffffff');
            bar.setAttribute('stroke-width', '1.5');
            bar.style.filter = 'brightness(1.35)';

            if (opticsTooltip) {
                const idx = bar.getAttribute('data-idx');
                const reach = bar.getAttribute('data-reach');
                const cluster = bar.getAttribute('data-cluster');
                const zone = bar.getAttribute('data-zone');
                const sub = bar.getAttribute('data-sub');
                const isNoise = bar.getAttribute('data-noise') === 'true';

                if (tooltipPointId) tooltipPointId.textContent = `Punto #${idx}`;
                if (tooltipZoneName) tooltipZoneName.textContent = zone || 'Zona Urbana';
                if (tooltipSubName) tooltipSubName.textContent = `Sub-Cluster: ${sub || 'General'}`;
                if (tooltipReachDist) tooltipReachDist.textContent = `Alcanzabilidad: ${reach} m`;

                if (tooltipClusterBadge) {
                    if (isNoise || cluster === '-1') {
                        tooltipClusterBadge.textContent = 'Pico Ruido (-1)';
                        tooltipClusterBadge.className = 'px-1.5 py-0.2 rounded text-[10px] font-bold bg-slate-700 text-slate-300';
                    } else {
                        tooltipClusterBadge.textContent = `Valle #${cluster}`;
                        tooltipClusterBadge.className = 'px-1.5 py-0.2 rounded text-[10px] font-bold bg-cyan-500/20 text-cyan-300';
                    }
                }

                // Posicionamiento dinámico del tooltip
                const svgRect = bar.closest('svg').getBoundingClientRect();
                const barRect = bar.getBoundingClientRect();
                const leftOffset = Math.max(10, Math.min(svgRect.width - 220, barRect.left - svgRect.left - 50));
                
                opticsTooltip.style.left = `${leftOffset}px`;
                opticsTooltip.style.top = `10px`;
                opticsTooltip.classList.remove('hidden');
            }
        });

        bar.addEventListener('mouseleave', () => {
            bar.removeAttribute('stroke');
            bar.removeAttribute('stroke-width');
            bar.style.filter = 'none';
            if (opticsTooltip) opticsTooltip.classList.add('hidden');
        });

        // Click en una barra para Brushing & Linking hacia la tabla y el mapa
        bar.addEventListener('click', () => {
            const cluster = bar.getAttribute('data-cluster');
            const zone = bar.getAttribute('data-zone');
            highlightZoneInUI(cluster, zone);
        });
    });

    // 8. Botones de Filtrado de Valles en la Leyenda
    const valleyFilterBtns = document.querySelectorAll('.optics-valley-filter-btn');
    valleyFilterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const valleyId = btn.getAttribute('data-valley-id');
            highlightValleyBars(valleyId);
        });
    });

    // Filas de Valles en la tabla de diagnóstico inferior
    const valleyRows = document.querySelectorAll('.valley-row');
    valleyRows.forEach(row => {
        row.addEventListener('click', () => {
            const vId = row.getAttribute('data-valley-id');
            highlightValleyBars(vId);
        });
    });

    // 9. Nodos del Mapa Táctico (Interacción bidireccional desde el Mapa)
    const mapNodes = document.querySelectorAll('[data-map-node]');
    mapNodes.forEach(node => {
        node.addEventListener('click', (e) => {
            if (wasTacticalMapDragged) return; // Si fue arrastre (pan), ignorar clic de selección
            const cluster = node.getAttribute('data-cluster');
            const name = node.getAttribute('data-name');
            highlightZoneInUI(cluster, name);
            highlightValleyBars(cluster);
        });
    });

    // 10. Controlador Táctico de Pan & Zoom del Mapa (Mover, Acercar, Achicar)
    const tacticalViewport = document.getElementById('tactical-map-viewport');
    const tacticalPanLayer = document.getElementById('tactical-map-panzoom-layer');
    const btnTacticalZoomIn = document.getElementById('btn-tactical-zoom-in');
    const btnTacticalZoomOut = document.getElementById('btn-tactical-zoom-out');
    const btnTacticalZoomReset = document.getElementById('btn-tactical-zoom-reset');
    const tacticalZoomBadge = document.getElementById('tactical-zoom-badge');

    let tacticalZoom = 1.0;
    let tacticalPanX = 0;
    let tacticalPanY = 0;
    let isTacticalPanning = false;
    let wasTacticalMapDragged = false;
    let panStartX = 0;
    let panStartY = 0;
    let clickStartX = 0;
    let clickStartY = 0;

    function applyTacticalPanZoom() {
        if (!tacticalPanLayer) return;
        // Transformación estándar SVG con zoom centrado en (500, 300) y traslación libre
        tacticalPanLayer.setAttribute(
            'transform',
            `translate(${tacticalPanX}, ${tacticalPanY}) translate(500, 300) scale(${tacticalZoom}) translate(-500, -300)`
        );
        if (tacticalZoomBadge) {
            tacticalZoomBadge.textContent = `${Math.round(tacticalZoom * 100)}%`;
        }
    }

    if (tacticalViewport && tacticalPanLayer) {
        // Mover (Arrastrar / Pan con el ratón)
        tacticalViewport.addEventListener('mousedown', (e) => {
            // Ignorar clic si es sobre botones o sliders del HUD o leyendas flotantes
            if (e.target.closest('#spatial-hud-box') || 
                e.target.closest('#tactical-zoom-dock') ||
                e.target.closest('#tactical-legend-dock') ||
                e.target.closest('button') ||
                e.target.closest('input')) {
                return;
            }

            e.preventDefault(); // Evitar selección de texto nativa del navegador para arrastre fluido
            isTacticalPanning = true;
            wasTacticalMapDragged = false;
            clickStartX = e.clientX;
            clickStartY = e.clientY;

            const rect = tacticalViewport.getBoundingClientRect();
            const svgScaleX = 1000 / (rect.width || 1000);
            const svgScaleY = 600 / (rect.height || 600);

            panStartX = (e.clientX * svgScaleX) - tacticalPanX;
            panStartY = (e.clientY * svgScaleY) - tacticalPanY;
            tacticalViewport.classList.remove('cursor-grab');
            tacticalViewport.classList.add('cursor-grabbing');
        });

        window.addEventListener('mousemove', (e) => {
            if (!isTacticalPanning) return;
            const dist = Math.hypot(e.clientX - clickStartX, e.clientY - clickStartY);
            if (dist > 4) {
                wasTacticalMapDragged = true;
            }

            const rect = tacticalViewport.getBoundingClientRect();
            const svgScaleX = 1000 / (rect.width || 1000);
            const svgScaleY = 600 / (rect.height || 600);

            tacticalPanX = (e.clientX * svgScaleX) - panStartX;
            tacticalPanY = (e.clientY * svgScaleY) - panStartY;
            applyTacticalPanZoom();
        });

        window.addEventListener('mouseup', () => {
            if (isTacticalPanning) {
                isTacticalPanning = false;
                if (tacticalViewport) {
                    tacticalViewport.classList.remove('cursor-grabbing');
                    tacticalViewport.classList.add('cursor-grab');
                }
            }
        });

        // Acercar / Achicar con la rueda del ratón (Mouse Wheel)
        tacticalViewport.addEventListener('wheel', (e) => {
            if (e.target.closest('#spatial-hud-box')) return;
            e.preventDefault();
            const zoomDelta = e.deltaY < 0 ? 0.15 : -0.15;
            const newZoom = Math.max(0.6, Math.min(4.0, Number((tacticalZoom + zoomDelta).toFixed(2))));

            const rect = tacticalViewport.getBoundingClientRect();
            const mouseSvgX = ((e.clientX - rect.left) / (rect.width || 1)) * 1000;
            const mouseSvgY = ((e.clientY - rect.top) / (rect.height || 1)) * 600;

            // Centrado relativo al cursor
            tacticalPanX -= (mouseSvgX - 500) * (newZoom / tacticalZoom - 1);
            tacticalPanY -= (mouseSvgY - 300) * (newZoom / tacticalZoom - 1);
            tacticalZoom = newZoom;

            applyTacticalPanZoom();
        }, { passive: false });

        // Soporte Táctil (Touch Pan & Pinch Zoom)
        let lastTouchDist = 0;
        let touchStartX = 0;
        let touchStartY = 0;

        tacticalViewport.addEventListener('touchstart', (e) => {
            if (e.target.closest('#spatial-hud-box') || e.target.closest('#tactical-zoom-dock')) return;

            if (e.touches.length === 1) {
                isTacticalPanning = true;
                wasTacticalMapDragged = false;
                const rect = tacticalViewport.getBoundingClientRect();
                const svgScaleX = 1000 / (rect.width || 1000);
                const svgScaleY = 600 / (rect.height || 600);
                touchStartX = (e.touches[0].clientX * svgScaleX) - tacticalPanX;
                touchStartY = (e.touches[0].clientY * svgScaleY) - tacticalPanY;
            } else if (e.touches.length === 2) {
                isTacticalPanning = false;
                lastTouchDist = Math.hypot(
                    e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY
                );
            }
        }, { passive: true });

        tacticalViewport.addEventListener('touchmove', (e) => {
            if (e.touches.length === 1 && isTacticalPanning) {
                wasTacticalMapDragged = true;
                const rect = tacticalViewport.getBoundingClientRect();
                const svgScaleX = 1000 / (rect.width || 1000);
                const svgScaleY = 600 / (rect.height || 600);
                tacticalPanX = (e.touches[0].clientX * svgScaleX) - touchStartX;
                tacticalPanY = (e.touches[0].clientY * svgScaleY) - touchStartY;
                applyTacticalPanZoom();
            } else if (e.touches.length === 2) {
                const dist = Math.hypot(
                    e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY
                );
                if (lastTouchDist > 0) {
                    const factor = dist / lastTouchDist;
                    tacticalZoom = Math.max(0.6, Math.min(4.0, Number((tacticalZoom * factor).toFixed(2))));
                    applyTacticalPanZoom();
                }
                lastTouchDist = dist;
            }
        }, { passive: true });

        tacticalViewport.addEventListener('touchend', () => {
            isTacticalPanning = false;
            lastTouchDist = 0;
        }, { passive: true });

        // Botones de Acercar / Achicar / Reset
        if (btnTacticalZoomIn) {
            btnTacticalZoomIn.addEventListener('click', (e) => {
                e.stopPropagation();
                tacticalZoom = Math.min(4.0, Number((tacticalZoom + 0.25).toFixed(2)));
                applyTacticalPanZoom();
            });
        }

        if (btnTacticalZoomOut) {
            btnTacticalZoomOut.addEventListener('click', (e) => {
                e.stopPropagation();
                tacticalZoom = Math.max(0.6, Number((tacticalZoom - 0.25).toFixed(2)));
                applyTacticalPanZoom();
            });
        }

        if (btnTacticalZoomReset) {
            btnTacticalZoomReset.addEventListener('click', (e) => {
                e.stopPropagation();
                tacticalZoom = 1.0;
                tacticalPanX = 0;
                tacticalPanY = 0;
                applyTacticalPanZoom();
            });
        }
    }

    function highlightValleyBars(valleyId) {
        bars.forEach(b => {
            const c = b.getAttribute('data-cluster');
            if (valleyId === 'all' || c === valleyId) {
                b.style.opacity = '1';
                b.style.filter = 'drop-shadow(0 0 4px currentColor)';
            } else {
                b.style.opacity = '0.2';
                b.style.filter = 'none';
            }
        });
    }

    function updateSideInspector(row, clusterId, zoneName, featureProps) {
        const sideZone = document.getElementById('side-inspector-zone');
        const sideBadge = document.getElementById('side-inspector-badge');
        const sideMacro = document.getElementById('side-inspector-macro');
        const sideVol = document.getElementById('side-inspector-vol');
        const sideDensity = document.getElementById('side-inspector-density');
        const sideDelito = document.getElementById('side-inspector-delito');
        const sideNocturno = document.getElementById('side-inspector-nocturno');
        const sideDbscan = document.getElementById('side-inspector-dbscan');
        const sideOptics = document.getElementById('side-inspector-optics');
        const sideHdbscan = document.getElementById('side-inspector-hdbscan');

        if (!sideZone) return;

        if (featureProps) {
            const zTitle = featureProps.zone || featureProps.city || zoneName || 'PUNTO GEOESPACIAL';
            sideZone.textContent = zTitle.toUpperCase();
            if (sideBadge) {
                const isCrit = featureProps.ward === 'A' || featureProps.dbscan === 0 || featureProps.dbscan === 2;
                sideBadge.textContent = isCrit ? 'ALERTA ROJA' : (featureProps.ward === 'B' ? 'PATRULLAJE DINÁMICO' : 'VIGILANCIA ALTA');
                sideBadge.className = isCrit 
                    ? 'px-2 py-0.5 rounded text-[10px] font-bold uppercase border bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-500/20 dark:text-rose-300 dark:border-rose-500/40'
                    : 'px-2 py-0.5 rounded text-[10px] font-bold uppercase border bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-500/20 dark:text-amber-300 dark:border-amber-500/40';
            }
            if (sideMacro) sideMacro.textContent = featureProps.ward_label || `Macro-Cluster ${featureProps.ward || 'A'}`;
            if (sideVol) sideVol.textContent = featureProps.date ? `${featureProps.date} (${featureProps.source || 'Prensa'})` : '1 reporte directo';
            if (sideDensity) sideDensity.textContent = featureProps.hdbscan_persistence ? `λ=${featureProps.hdbscan_persistence}` : (featureProps.dbscan !== -1 ? 'Núcleo Denso' : 'Ruido (-1)');
            if (sideDelito) {
                const del = featureProps.category || featureProps.title || 'Incidente Reportado';
                sideDelito.textContent = del;
                sideDelito.title = del;
            }
            if (sideNocturno) sideNocturno.textContent = featureProps.date || 'N/D';
            if (sideDbscan) sideDbscan.textContent = featureProps.dbscan_label || (featureProps.dbscan !== undefined ? `DBSCAN #${featureProps.dbscan}` : `Cluster #${clusterId}`);
            if (sideOptics) sideOptics.textContent = featureProps.reach_depth_m ? `Valle ${featureProps.reach_depth_m}m` : `OPTICS ξ`;
            if (sideHdbscan) sideHdbscan.textContent = featureProps.hdbscan_label || (featureProps.hdbscan !== undefined ? `HDB #${featureProps.hdbscan}` : 'Estable');
            return;
        }

        if (row) {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 10) {
                const code = cells[0].textContent.trim();
                const name = cells[1].textContent.trim();
                const macro = cells[2].textContent.trim();
                const delito = cells[3].textContent.trim();
                const vol = cells[4].textContent.trim();
                const density = cells[5].textContent.trim();
                const nocturno = cells[6].textContent.trim();
                const dbscan = cells[7].textContent.trim();
                const optics = cells[8].textContent.trim().replace(/\s+/g, ' ');
                const status = cells[9].textContent.trim();

                sideZone.textContent = `${code}: ${name}`;
                if (sideBadge) {
                    sideBadge.textContent = status;
                    if (status.includes('ROJA')) {
                        sideBadge.className = 'px-2 py-0.5 rounded text-[10px] font-bold uppercase border bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-500/20 dark:text-rose-300 dark:border-rose-500/40';
                    } else if (status.includes('VIGILANCIA')) {
                        sideBadge.className = 'px-2 py-0.5 rounded text-[10px] font-bold uppercase border bg-cyan-100 text-cyan-800 border-cyan-300 dark:bg-cyan-500/20 dark:text-cyan-300 dark:border-cyan-500/40';
                    } else if (status.includes('DINÁMICO') || status.includes('ALERTA')) {
                        sideBadge.className = 'px-2 py-0.5 rounded text-[10px] font-bold uppercase border bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-500/20 dark:text-amber-300 dark:border-amber-500/40';
                    } else {
                        sideBadge.className = 'px-2 py-0.5 rounded text-[10px] font-bold uppercase border bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-500/20 dark:text-emerald-300 dark:border-emerald-500/40';
                    }
                }
                if (sideMacro) sideMacro.textContent = macro;
                if (sideVol) sideVol.textContent = vol;
                if (sideDensity) sideDensity.textContent = density;
                if (sideDelito) {
                    sideDelito.textContent = delito;
                    sideDelito.title = delito;
                }
                if (sideNocturno) sideNocturno.textContent = nocturno;
                if (sideDbscan) sideDbscan.textContent = dbscan;
                if (sideOptics) sideOptics.textContent = optics;
                if (sideHdbscan) sideHdbscan.textContent = `Estable // ${macro}`;
                return;
            }
        }

        if (zoneName) {
            sideZone.textContent = zoneName.toUpperCase();
            if (sideDbscan) sideDbscan.textContent = `Hotspot #${clusterId}`;
            if (sideOptics) sideOptics.textContent = `Valle #${clusterId} (OPTICS ξ)`;
        }
    }

    function highlightZoneInUI(clusterId, zoneName) {
        // Resaltar fila en la tabla de taxonomía
        const zoneRows = document.querySelectorAll('.zone-row');
        let matchedRow = null;
        zoneRows.forEach(r => {
            const rText = r.textContent.toLowerCase();
            const zName = zoneName ? zoneName.toLowerCase().split(' ')[0] : '';
            if (zName && rText.includes(zName)) {
                r.classList.add('bg-primary-container/20', 'border-l-4', 'border-primary-container');
                r.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                matchedRow = r;
            } else {
                r.classList.remove('bg-primary-container/20', 'border-l-4', 'border-primary-container');
            }
        });

        // Actualizar el Inspector Táctico Lateral
        updateSideInspector(matchedRow, clusterId, zoneName);
    }

    // Eventos de Clic en Filas de Taxonomía y Valles
    document.querySelectorAll('.zone-row').forEach(row => {
        row.addEventListener('click', () => {
            const cluster = row.getAttribute('data-cluster') || '0';
            const nameCell = row.querySelectorAll('td')[1];
            const name = nameCell ? nameCell.textContent.trim() : '';
            highlightZoneInUI(cluster, name);
        });
    });

    document.querySelectorAll('.valley-row').forEach(row => {
        row.addEventListener('click', () => {
            const valleyId = row.getAttribute('data-valley-id');
            if (valleyId) highlightValleyBars(valleyId);
            const nameCell = row.querySelectorAll('td')[1];
            const name = nameCell ? nameCell.textContent.trim() : '';
            highlightZoneInUI(valleyId, name);
        });
    });

    // 12. Conmutador Interactivo de Tarjetas Analíticas (DBSCAN / HDBSCAN / OPTICS)
    const algoCards = document.querySelectorAll('[data-algo-card]');
    const algoPanels = {
        'dbscan': document.getElementById('panel-algo-dbscan'),
        'hdbscan': document.getElementById('panel-algo-hdbscan'),
        'optics': document.getElementById('panel-algo-optics')
    };

    algoCards.forEach(card => {
        card.addEventListener('click', () => {
            const selectedAlgo = card.getAttribute('data-algo-card');

            // Actualizar estilo visual de las 3 tarjetas
            algoCards.forEach(c => {
                c.classList.remove(
                    'active', 'bg-surface-container-high',
                    'border-cyan-400', 'border-emerald-400', 'border-amber-400',
                    'shadow-[0_0_15px_rgba(0,229,255,0.18)]',
                    'shadow-[0_0_15px_rgba(52,211,153,0.18)]',
                    'shadow-[0_0_15px_rgba(251,191,36,0.18)]'
                );
                c.classList.add('bg-surface-container', 'border-outline-variant/60');
                const badge = c.querySelector('.card-status-badge');
                if (badge) badge.classList.add('hidden');
            });

            card.classList.remove('bg-surface-container', 'border-outline-variant/60');
            card.classList.add('active', 'bg-surface-container-high');

            if (selectedAlgo === 'hdbscan') {
                card.classList.add('border-emerald-400', 'shadow-[0_0_15px_rgba(52,211,153,0.18)]');
            } else if (selectedAlgo === 'optics') {
                card.classList.add('border-amber-400', 'shadow-[0_0_15px_rgba(251,191,36,0.18)]');
            } else {
                card.classList.add('border-cyan-400', 'shadow-[0_0_15px_rgba(0,229,255,0.18)]');
            }

            const activeBadge = card.querySelector('.card-status-badge');
            if (activeBadge) activeBadge.classList.remove('hidden');

            // Conmutar visibilidad de los paneles inferiores
            Object.keys(algoPanels).forEach(key => {
                const panel = algoPanels[key];
                if (panel) {
                    if (key === selectedAlgo) {
                        panel.classList.remove('hidden');
                    } else {
                        panel.classList.add('hidden');
                    }
                }
            });

            // Sincronizar capa en el visor cartográfico superior
            const layerBtn = document.querySelector(`[data-layer-toggle="${selectedAlgo}"]`);
            if (layerBtn && !layerBtn.classList.contains('active-layer')) {
                layerBtn.click();
            }
        });
    });

    // 13. Selector de Métodos de Enlace (Linkage Criteria)
    const linkageButtons = document.querySelectorAll('.btn-linkage');
    const copheneticValEl = document.getElementById('dendro-cophenetic-val');
    const linkageDescEl = document.getElementById('dendro-linkage-desc');

    linkageButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            linkageButtons.forEach(b => {
                b.classList.remove('bg-primary-container', 'text-on-primary', 'shadow-sm');
                b.classList.add('text-outline');
            });
            btn.classList.add('bg-primary-container', 'text-on-primary', 'shadow-sm');
            btn.classList.remove('text-outline');

            const rVal = btn.getAttribute('data-r');
            const desc = btn.getAttribute('data-desc');

            if (copheneticValEl) copheneticValEl.textContent = `r = ${rVal}`;
            if (linkageDescEl) linkageDescEl.textContent = desc;
        });
    });

    // 14. Toggle de Vistas (Dendrograma SVG vs Matriz Clustermap)
    const btnViewDendro = document.getElementById('btn-view-dendrogram');
    const btnViewCluster = document.getElementById('btn-view-clustermap');
    const dendroTreeView = document.getElementById('dendrogram-tree-view');
    const dendroClustermapView = document.getElementById('dendrogram-clustermap-view');

    if (btnViewDendro && btnViewCluster && dendroTreeView && dendroClustermapView) {
        btnViewDendro.addEventListener('click', () => {
            btnViewDendro.classList.add('bg-primary-container', 'text-on-primary', 'shadow-sm');
            btnViewDendro.classList.remove('bg-surface-container', 'text-outline');
            btnViewCluster.classList.remove('bg-primary-container', 'text-on-primary', 'shadow-sm');
            btnViewCluster.classList.add('bg-surface-container', 'text-outline');

            dendroTreeView.classList.remove('hidden');
            dendroClustermapView.classList.add('hidden');
        });

        btnViewCluster.addEventListener('click', () => {
            btnViewCluster.classList.add('bg-primary-container', 'text-on-primary', 'shadow-sm');
            btnViewCluster.classList.remove('bg-surface-container', 'text-outline');
            btnViewDendro.classList.remove('bg-primary-container', 'text-on-primary', 'shadow-sm');
            btnViewDendro.classList.add('bg-surface-container', 'text-outline');

            dendroClustermapView.classList.remove('hidden');
            dendroTreeView.classList.add('hidden');
        });
    }

    // 15. Control Deslizante de Umbral de Corte Cofenético (t)
    const sliderThreshold = document.getElementById('slider-dendro-threshold');
    const cutLine = document.getElementById('dendro-cut-line');
    const cutText = document.getElementById('dendro-cut-text');
    const valThresholdEl = document.getElementById('val-dendro-threshold');
    const valClustersEl = document.getElementById('val-dendro-clusters');

    if (sliderThreshold && cutLine && cutText) {
        sliderThreshold.addEventListener('input', () => {
            const t = parseFloat(sliderThreshold.value);
            let ySvg = 75;
            let k = 3;

            if (currentCtx === 'chicago') {
                ySvg = 140 - ((t - 15) / 65) * 115;
                if (t >= 60) k = 2;
                else if (t >= 35) k = 3;
                else if (t >= 25) k = 4;
                else k = 6;
            } else {
                ySvg = 140 - ((t - 5) / 25) * 110;
                if (t >= 18) k = 2;
                else if (t >= 10) k = 3;
                else if (t >= 7) k = 4;
                else k = 6;
            }

            cutLine.setAttribute('y1', ySvg);
            cutLine.setAttribute('y2', ySvg);
            cutText.setAttribute('y', ySvg - 5);
            cutText.textContent = `Corte t=${t.toFixed(1)} (k=${k})`;

            if (valThresholdEl) valThresholdEl.textContent = `t = ${t.toFixed(1)}`;
            if (valClustersEl) valClustersEl.textContent = `k = ${k} Macro-Grupos`;
        });
    }

    // 16. Brushing & Linking (Dendrograma <-> Mapa <-> Tabla)
    const branchGroups = document.querySelectorAll('.dendro-branch-group, .dendro-badge-card');
    const zoneTableRows = document.querySelectorAll('.zone-row');

    branchGroups.forEach(bg => {
        bg.addEventListener('mouseenter', () => {
            const branch = bg.getAttribute('data-branch');
            zoneTableRows.forEach(row => {
                const text = row.textContent;
                if (text.includes(`Cluster ${branch}`) || 
                    (branch === 'A' && (text.includes('Harrison') || text.includes('Santa Cruz'))) || 
                    (branch === 'B' && (text.includes('Central') || text.includes('Cochabamba') || text.includes('Plan 3000'))) || 
                    (branch === 'C' && (text.includes('Jefferson') || text.includes('Equipetrol') || text.includes('La Paz')))) {
                    row.classList.add('bg-primary-container/20', 'border-l-4', 'border-primary-container');
                }
            });

            const matchedBranches = document.querySelectorAll(`.dendro-branch-group[data-branch="${branch}"] path`);
            matchedBranches.forEach(p => {
                p.style.strokeWidth = '4px';
                p.style.filter = 'drop-shadow(0 0 6px currentColor)';
            });
        });

        bg.addEventListener('mouseleave', () => {
            zoneTableRows.forEach(row => {
                row.classList.remove('bg-primary-container/20', 'border-l-4', 'border-primary-container');
            });

            const allPaths = document.querySelectorAll('.dendro-branch-group path');
            allPaths.forEach(p => {
                p.style.strokeWidth = '';
                p.style.filter = '';
            });
        });
    });

    // =========================================================================
    // 17. CONMUTADOR DUAL-MODE (2D TÁCTICO SVG <-> GLOBO 3D WEBGIS MAPLIBRE GL)
    // =========================================================================
    const btnView2D = document.getElementById('btn-view-2d');
    const btnView3D = document.getElementById('btn-view-3d');
    const viewport2D = document.getElementById('tactical-map-viewport');
    const viewport3D = document.getElementById('tactical-map-viewport-3d');
    const layersBar2D = document.getElementById('tactical-2d-layers-bar');

    let map3dInstance = null;
    let isGlobe3DInitialized = false;
    let currentGlobeMode = 'dbscan';

    function setDualView(mode) {
        if (mode === '3d') {
            if (btnView3D) {
                btnView3D.classList.add('bg-primary-container', 'text-on-primary', 'shadow-xs', 'active');
                btnView3D.classList.remove('text-on-surface-variant');
            }
            if (btnView2D) {
                btnView2D.classList.remove('bg-primary-container', 'text-on-primary', 'shadow-xs', 'active');
                btnView2D.classList.add('text-on-surface-variant');
            }
            if (viewport2D) viewport2D.classList.add('hidden');
            if (viewport3D) viewport3D.classList.remove('hidden');
            if (layersBar2D) layersBar2D.classList.add('opacity-40', 'pointer-events-none');

            initOrResizeGlobe3D();
        } else {
            if (btnView2D) {
                btnView2D.classList.add('bg-primary-container', 'text-on-primary', 'shadow-xs', 'active');
                btnView2D.classList.remove('text-on-surface-variant');
            }
            if (btnView3D) {
                btnView3D.classList.remove('bg-primary-container', 'text-on-primary', 'shadow-xs', 'active');
                btnView3D.classList.add('text-on-surface-variant');
            }
            if (viewport2D) viewport2D.classList.remove('hidden');
            if (viewport3D) viewport3D.classList.add('hidden');
            if (layersBar2D) layersBar2D.classList.remove('opacity-40', 'pointer-events-none');
        }
    }

    if (btnView2D) btnView2D.addEventListener('click', () => setDualView('2d'));
    if (btnView3D) btnView3D.addEventListener('click', () => setDualView('3d'));

    // =========================================================================
    // 18. MOTOR GLOBO 3D WEBGIS // MAPLIBRE GL JS v4 ULTRALIGERO
    // =========================================================================
    function getGlobeColorExpression(mode) {
        if (mode === 'ward') {
            return ['coalesce', ['get', 'ward_color'], '#ff3366'];
        }
        if (mode === 'optics') {
            return ['coalesce', ['get', 'optics_color'], '#38bdf8'];
        }
        if (mode === 'hdbscan') {
            return ['coalesce', ['get', 'hdbscan_color'], '#34d399'];
        }
        // DBSCAN por defecto
        return ['coalesce', ['get', 'dbscan_color'], '#00e5ff'];
    }

    function initOrResizeGlobe3D() {
        if (typeof maplibregl === 'undefined') {
            console.warn('[WebGIS 3D] MapLibre GL no está disponible en la página.');
            return;
        }

        if (isGlobe3DInitialized && map3dInstance) {
            setTimeout(() => {
                map3dInstance.resize();
            }, 60);
            return;
        }

        const isChicago = (currentCtx === 'chicago');
        const initialCenter = isChicago ? [-87.6298, 41.8781] : [-64.2, -17.2];
        const initialZoom = isChicago ? 10.5 : 5.4;

        try {
            map3dInstance = new maplibregl.Map({
                container: 'maplibre-3d-canvas',
                style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
                center: initialCenter,
                zoom: initialZoom,
                pitch: 42,
                bearing: isChicago ? -10 : -8,
                scrollZoom: false, // Prevención estricta de atrapamiento de rueda
                cooperativeGestures: true // Requiere Ctrl + Scroll para zoom si se usa la rueda
            });

            isGlobe3DInitialized = true;

            map3dInstance.on('load', () => {
                // Configurar proyección esférica si está soportada en v4+
                if (typeof map3dInstance.setProjection === 'function') {
                    try {
                        map3dInstance.setProjection({ type: 'globe' });
                    } catch (e) {
                        console.log('[WebGIS 3D] Proyección esférica fallback');
                    }
                }

                // Cargar datos GeoJSON desde la API Flask
                const geojsonUrl = `/api/v1/webgis/geojson?ctx=${encodeURIComponent(currentCtx)}`;

                fetch(geojsonUrl)
                    .then(res => res.json())
                    .then(data => {
                        const countEl = document.getElementById('globe-3d-stat-points');
                        if (countEl && data.total) {
                            countEl.textContent = `${data.total} hechos`;
                        }

                        // 1. Fuente con clustering para halos
                        map3dInstance.addSource('webgis-3d-events', {
                            type: 'geojson',
                            data: data,
                            cluster: true,
                            clusterMaxZoom: 12,
                            clusterRadius: 35
                        });

                        // 2. Fuente continua sin clustering para garantizar puntos siempre visibles a todo zoom
                        map3dInstance.addSource('webgis-3d-raw', {
                            type: 'geojson',
                            data: data,
                            cluster: false
                        });

                        // Halos de Clústeres (translúcidos)
                        map3dInstance.addLayer({
                            id: 'clusters-halo-3d',
                            type: 'circle',
                            source: 'webgis-3d-events',
                            filter: ['has', 'point_count'],
                            paint: {
                                'circle-color': [
                                    'step',
                                    ['get', 'point_count'],
                                    'rgba(0, 229, 255, 0.35)',
                                    5, 'rgba(251, 191, 36, 0.35)',
                                    15, 'rgba(255, 51, 102, 0.40)'
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

                        // Núcleo sólido de clústeres
                        map3dInstance.addLayer({
                            id: 'clusters-core-3d',
                            type: 'circle',
                            source: 'webgis-3d-events',
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
                                    14,
                                    5, 18,
                                    15, 24
                                ],
                                'circle-stroke-width': 2,
                                'circle-stroke-color': '#0f172a'
                            }
                        });

                        // Conteo numérico de clústeres (sin text-font rígido para máxima compatibilidad)
                        map3dInstance.addLayer({
                            id: 'cluster-count-3d',
                            type: 'symbol',
                            source: 'webgis-3d-events',
                            filter: ['has', 'point_count'],
                            layout: {
                                'text-field': '{point_count_abbreviated}',
                                'text-size': 12
                            },
                            paint: {
                                'text-color': '#ffffff'
                            }
                        });

                        // Puntos individuales continuos: SIEMPRE VISIBLES a cualquier nivel de zoom
                        map3dInstance.addLayer({
                            id: 'raw-points-3d',
                            type: 'circle',
                            source: 'webgis-3d-raw',
                            paint: {
                                'circle-color': getGlobeColorExpression(currentGlobeMode),
                                'circle-radius': [
                                    'interpolate', ['linear'], ['zoom'],
                                    2, 5.5,
                                    5, 8.0,
                                    10, 10.5,
                                    14, 13.0
                                ],
                                'circle-stroke-width': 2.2,
                                'circle-stroke-color': '#ffffff',
                                'circle-opacity': 0.95
                            }
                        });

                        // Clic en clúster: zoom in suave
                        map3dInstance.on('click', 'clusters-core-3d', (e) => {
                            const features = map3dInstance.queryRenderedFeatures(e.point, { layers: ['clusters-core-3d'] });
                            if (!features || !features.length) return;
                            const clusterId = features[0].properties.cluster_id;
                            map3dInstance.getSource('webgis-3d-events').getClusterExpansionZoom(clusterId, (err, zoom) => {
                                if (err) return;
                                map3dInstance.easeTo({
                                    center: features[0].geometry.coordinates,
                                    zoom: zoom + 0.8
                                });
                            });
                        });

                        // Clic en punto individual continuo: sincronizar Inspector Lateral
                        map3dInstance.on('click', 'raw-points-3d', (e) => {
                            if (!e.features || !e.features[0]) return;
                            const feat = e.features[0];
                            const props = feat.properties;

                            // Actualizar Inspector Lateral
                            updateSideInspector(null, props.dbscan !== undefined ? props.dbscan : props.cluster, props.city || props.zone || props.category, props);

                            // Efecto de pulso en Inspector
                            const panel = document.getElementById('spatial-inspector-panel');
                            if (panel) {
                                panel.classList.add('ring-2', 'ring-cyan-400');
                                setTimeout(() => panel.classList.remove('ring-2', 'ring-cyan-400'), 1200);
                            }
                        });

                        // Cambiar cursor al pasar sobre elementos interactivos
                        map3dInstance.on('mouseenter', 'raw-points-3d', () => {
                            map3dInstance.getCanvas().style.cursor = 'pointer';
                        });
                        map3dInstance.on('mouseleave', 'raw-points-3d', () => {
                            map3dInstance.getCanvas().style.cursor = '';
                        });
                        map3dInstance.on('mouseenter', 'clusters-core-3d', () => {
                            map3dInstance.getCanvas().style.cursor = 'pointer';
                        });
                        map3dInstance.on('mouseleave', 'clusters-core-3d', () => {
                            map3dInstance.getCanvas().style.cursor = '';
                        });
                    })
                    .catch(err => console.error('[WebGIS 3D] Error cargando GeoJSON:', err));
            });

            // Controles de navegación 3D
            const btnZoomIn = document.getElementById('btn-globe-zoom-in');
            const btnZoomOut = document.getElementById('btn-globe-zoom-out');
            const btnReset = document.getElementById('btn-globe-reset');
            const btnPitch = document.getElementById('btn-globe-pitch');

            if (btnZoomIn) btnZoomIn.addEventListener('click', () => map3dInstance.zoomIn());
            if (btnZoomOut) btnZoomOut.addEventListener('click', () => map3dInstance.zoomOut());
            if (btnReset) btnReset.addEventListener('click', () => {
                map3dInstance.flyTo({
                    center: initialCenter,
                    zoom: initialZoom,
                    pitch: 42,
                    bearing: isChicago ? -10 : -8,
                    speed: 1.2
                });
            });

            let currentPitch = 42;
            if (btnPitch) btnPitch.addEventListener('click', () => {
                currentPitch = currentPitch === 42 ? 65 : (currentPitch === 65 ? 0 : 42);
                map3dInstance.easeTo({ pitch: currentPitch, duration: 600 });
            });

            // Botones de modo algorítmico 3D
            document.querySelectorAll('.globe-mode-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.globe-mode-btn').forEach(b => {
                        b.classList.remove('bg-cyan-500/20', 'text-cyan-300', 'border-cyan-500/40', 'font-bold', 'active');
                        b.classList.add('bg-surface-container', 'text-slate-300', 'border-outline-variant');
                    });
                    btn.classList.add('bg-cyan-500/20', 'text-cyan-300', 'border-cyan-500/40', 'font-bold', 'active');
                    btn.classList.remove('bg-surface-container', 'text-slate-300', 'border-outline-variant');

                    const mode = btn.getAttribute('data-globe-mode');
                    currentGlobeMode = mode;

                    if (map3dInstance && map3dInstance.getLayer('raw-points-3d')) {
                        map3dInstance.setPaintProperty(
                            'raw-points-3d',
                            'circle-color',
                            getGlobeColorExpression(mode)
                        );
                    }
                });
            });

        } catch (e) {
            console.error('[WebGIS 3D] Error inicializando MapLibre GL:', e);
        }
    }
});
