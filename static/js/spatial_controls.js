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

    // 4. Parámetros Espaciales y Filtros del Mapa Táctico (DBSCAN, Franja, Delito)
    const btnApplyFilter = document.getElementById('btn-apply-spatial-filter');
    const btnResetFilter = document.getElementById('btn-reset-spatial-filter');
    const selectFranja = document.getElementById('filter-franja-horaria');
    const selectCrime = document.getElementById('filter-crime-type');

    // Slider de radio eps: solo actualiza la lectura numérica en metros sin recalcular
    if (epsSlider) {
        epsSlider.addEventListener('input', () => {
            const eps = parseInt(epsSlider.value);
            if (epsValDisplay) {
                epsValDisplay.textContent = `${eps} m`;
            }
        });
    }

    async function applySpatialFilter() {
        if (!epsSlider) return;
        const eps = parseInt(epsSlider.value);
        const minPts = parseInt(epsSlider.getAttribute('data-default-min-pts') || (currentCtx === 'chicago' ? 25 : 5));
        const franja = selectFranja ? selectFranja.value : 'todo';
        const delito = selectCrime ? selectCrime.value : 'todos';

        const activeLayers = [];
        document.querySelectorAll('[data-layer-toggle]').forEach(btn => {
            if (btn.classList.contains('active-layer')) {
                activeLayers.push(btn.getAttribute('data-layer-toggle'));
            }
        });

        const samplingText = document.getElementById('map-sampling-text');
        const applyBtn = document.getElementById('btn-apply-spatial-filter');

        if (applyBtn) {
            applyBtn.classList.add('opacity-60', 'pointer-events-none');
        }

        try {
            const query = new URLSearchParams({
                ctx: currentCtx,
                eps: eps.toString(),
                min_pts: minPts.toString(),
                franja: franja,
                delito: delito,
                layers: activeLayers.join(',')
            });

            const res = await fetch(`/api/v1/spatial_filter?${query.toString()}`);
            const data = await res.json();

            if (data.sampling && samplingText) {
                samplingText.textContent = data.sampling.label;
            }

            if (data.active_hotspots !== undefined && hotspotsCountDisplay) {
                hotspotsCountDisplay.textContent = `${data.active_hotspots} zonas`;
            }

            if (data.noise_count !== undefined && noiseCountDisplay) {
                noiseCountDisplay.textContent = `${data.noise_count} pts`;
            }

            // Actualizar radios dinámicos de hotspots si vienen en data.layers_data
            if (data.layers_data && data.layers_data.hotspots) {
                const dbscanLayer = document.getElementById(currentCtx === 'chicago' ? 'layer-dbscan-chicago' : 'layer-dbscan-bolivia');
                if (dbscanLayer) {
                    const circles = dbscanLayer.querySelectorAll('circle');
                    data.layers_data.hotspots.forEach((h, idx) => {
                        const targetCircle = circles[idx * 2];
                        if (targetCircle && h.r) {
                            targetCircle.setAttribute('r', h.r);
                        }
                    });
                }
            }
        } catch (e) {
            console.error("Error al aplicar filtros espaciales:", e);
        } finally {
            if (applyBtn) {
                applyBtn.classList.remove('opacity-60', 'pointer-events-none');
            }
        }
    }

    function resetSpatialFilter() {
        if (!epsSlider) return;
        const defaultEps = epsSlider.getAttribute('data-default-eps') || (currentCtx === 'chicago' ? 300 : 2500);
        epsSlider.value = defaultEps;
        if (epsValDisplay) {
            epsValDisplay.textContent = `${defaultEps} m`;
        }

        if (selectFranja && !selectFranja.disabled) {
            selectFranja.value = 'todo';
        }

        if (selectCrime) {
            selectCrime.selectedIndex = 0;
        }

        // Restablecer todas las capas a activas
        document.querySelectorAll('[data-layer-toggle]').forEach(btn => {
            btn.classList.add('active-layer');
            btn.style.opacity = '1';
            const icon = btn.querySelector('.material-symbols-outlined');
            if (icon) icon.textContent = 'check_box';
            const layerType = btn.getAttribute('data-layer-toggle');
            setLayerVisibility(layerType, true);
        });

        applySpatialFilter();
    }

    if (btnApplyFilter) btnApplyFilter.addEventListener('click', applySpatialFilter);
    if (btnResetFilter) btnResetFilter.addEventListener('click', resetSpatialFilter);
    if (selectFranja) selectFranja.addEventListener('change', applySpatialFilter);
    if (selectCrime) selectCrime.addEventListener('change', applySpatialFilter);

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
                btn.classList.remove('active-layer');
                btn.style.opacity = '0.40';
                if (icon) icon.textContent = 'check_box_outline_blank';
                setLayerVisibility(layerType, false);
            } else {
                btn.classList.add('active-layer');
                btn.style.opacity = '1';
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

        // Click en una barra para Brushing & Linking hacia el mapa táctico y la tabla
        bar.addEventListener('click', (e) => {
            e.stopPropagation();
            const cluster = bar.getAttribute('data-cluster');
            const zone = bar.getAttribute('data-zone');
            highlightValleyOnMap(cluster, zone);
            highlightZoneInUI(cluster, zone);
        });
    });

    // 8. Mini-barras y Botones de Filtrado de Valles OPTICS
    const miniReachBars = document.querySelectorAll('.mini-reach-bar');
    miniReachBars.forEach(b => {
        b.addEventListener('click', (e) => {
            e.stopPropagation();
            const valleyId = b.getAttribute('data-mini-valley');
            const name = b.getAttribute('data-mini-name');
            highlightValleyOnMap(valleyId, name);
            highlightValleyBars(valleyId);
        });
    });

    const valleyFilterBtns = document.querySelectorAll('.optics-valley-filter-btn');
    valleyFilterBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const valleyId = btn.getAttribute('data-valley-id');
            highlightValleyBars(valleyId);
            highlightValleyOnMap(valleyId, null);
        });
    });

    // Filas de Valles en la tabla de diagnóstico inferior
    const valleyRows = document.querySelectorAll('.valley-row');
    valleyRows.forEach(row => {
        row.addEventListener('click', (e) => {
            e.stopPropagation();
            const vId = row.getAttribute('data-valley-id');
            highlightValleyBars(vId);
            highlightValleyOnMap(vId, null);
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
                e.target.closest('#tactical-inspector-card') || 
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
            if (e.target.closest('#spatial-hud-box') || e.target.closest('#tactical-inspector-card')) return;
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
            if (e.target.closest('#spatial-hud-box') || e.target.closest('#tactical-inspector-card') || e.target.closest('#tactical-zoom-dock')) return;

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

        // Actualizar Inspector Card
        const inspectorCard = document.getElementById('tactical-inspector-card');
        const inspectorTitle = document.getElementById('inspector-title');
        const inspectorBadge = document.getElementById('inspector-badge');
        if (inspectorTitle && inspectorCard) {
            inspectorTitle.textContent = `VALLE OPTICS #${valleyId}`;
            if (inspectorBadge) {
                inspectorBadge.textContent = 'CUENCA ENFOCADA';
            }
        }
    }

    function highlightValleyOnMap(valleyId, zoneName) {
        clearMapValleyHighlight();

        if (!valleyId || valleyId === '-1' || valleyId === -1) {
            return;
        }

        const vStr = valleyId.toString();
        const nodes = document.querySelectorAll(`#tactical-map-svg [data-cluster="${vStr}"]`);
        nodes.forEach(node => {
            node.classList.add('valley-map-highlighted');
            node.setAttribute('stroke', '#fbbf24');
            node.setAttribute('stroke-width', '4');
            node.style.filter = 'drop-shadow(0 0 12px #fbbf24)';
        });

        // Feedback en el Inspector Card Táctico
        const inspectorTitle = document.getElementById('inspector-title');
        const inspectorBadge = document.getElementById('inspector-badge');
        const inspectorVol = document.getElementById('inspector-vol');
        if (inspectorTitle) {
            inspectorTitle.textContent = zoneName ? zoneName.toUpperCase() : `VALLE OPTICS #${vStr}`;
        }
        if (inspectorBadge) {
            inspectorBadge.textContent = 'CUENCA ENFOCADA';
            inspectorBadge.className = 'px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px] font-bold';
        }
        if (inspectorVol) {
            inspectorVol.textContent = `Cuenca &xi; seleccionada`;
        }

        // Desplazar suavemente hacia la sección #mapa
        const mapSection = document.getElementById('mapa');
        if (mapSection) {
            mapSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    function clearMapValleyHighlight() {
        const highlighted = document.querySelectorAll('#tactical-map-svg .valley-map-highlighted');
        highlighted.forEach(el => {
            el.classList.remove('valley-map-highlighted');
            el.style.filter = '';
            const cluster = el.getAttribute('data-cluster');
            if (cluster === '1' || cluster === '0') el.setAttribute('stroke', '#00e5ff');
            else if (cluster === '2') el.setAttribute('stroke', '#ff3366');
            else if (cluster === '3' || cluster === '7') el.setAttribute('stroke', '#34d399');
            else if (cluster === '5') el.setAttribute('stroke', '#818cf8');
            else el.setAttribute('stroke', '#38bdf8');
            el.setAttribute('stroke-width', '1.8');
        });
    }

    // Clic fuera del valle en el mapa para quitar el resalte
    const mapViewportEl = document.getElementById('tactical-map-viewport');
    if (mapViewportEl) {
        mapViewportEl.addEventListener('click', (e) => {
            if (!e.target.closest('[data-map-node]') && !e.target.closest('[data-cluster]')) {
                clearMapValleyHighlight();
                const bars = document.querySelectorAll('.optics-bar');
                bars.forEach(b => {
                    b.style.opacity = b.getAttribute('data-noise') === 'true' ? '0.40' : '0.90';
                    b.style.filter = 'none';
                });
            }
        });
    }

    function highlightZoneInUI(clusterId, zoneName) {
        // Resaltar fila en la tabla de taxonomía
        const zoneRows = document.querySelectorAll('.zone-row');
        zoneRows.forEach(r => {
            const rText = r.textContent.toLowerCase();
            if (zoneName && rText.includes(zoneName.toLowerCase().split(' ')[0])) {
                r.classList.add('bg-primary-container/20', 'border-l-4', 'border-primary-container');
                r.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            } else {
                r.classList.remove('bg-primary-container/20', 'border-l-4', 'border-primary-container');
            }
        });

        // Feedback en el Inspector Card Táctico
        const inspectorTitle = document.getElementById('inspector-title');
        const inspectorVol = document.getElementById('inspector-vol');
        if (inspectorTitle) {
            inspectorTitle.textContent = zoneName ? zoneName.toUpperCase() : `CLUSTER #${clusterId}`;
        }
        if (inspectorVol) {
            inspectorVol.textContent = `Valle #${clusterId} (OPTICS &xi;)`;
        }
    }

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

    // 13. Selector de Métodos de Enlace (Linkage Criteria) y Actualización Dinámica
    const linkageButtons = document.querySelectorAll('.btn-linkage');
    const copheneticValEl = document.getElementById('dendro-cophenetic-val');
    const copheneticDirectEl = document.getElementById('dendro-cophenetic-direct');
    const linkageDescEl = document.getElementById('dendro-linkage-desc');
    const sliderThreshold = document.getElementById('slider-dendro-threshold');
    const cutLine = document.getElementById('dendro-cut-line');
    const cutText = document.getElementById('dendro-cut-text');
    const valThresholdEl = document.getElementById('val-dendro-threshold');
    const valClustersEl = document.getElementById('val-dendro-clusters');
    const dendroLinksGroup = document.getElementById('dendro-links-group');
    const dendroLeavesGroup = document.getElementById('dendro-leaves-group');
    const dendroLeafLabels = document.getElementById('dendro-leaf-labels');
    const clustermapTbody = document.getElementById('clustermap-tbody');
    const taxonomyGroupCards = document.getElementById('taxonomy-group-cards');

    let currentLinkage = 'ward';

    function updateTaxonomyUI(data) {
        if (!data || data.status !== 'ok') return;

        if (copheneticValEl) copheneticValEl.textContent = `r = ${data.cophenetic_r}`;
        if (copheneticDirectEl) copheneticDirectEl.textContent = `(sin Hellinger: ${data.cophenetic_direct_r})`;

        if (sliderThreshold) {
            sliderThreshold.min = data.min_t;
            sliderThreshold.max = data.max_t;
            sliderThreshold.step = data.step_t;
            sliderThreshold.value = data.active_t;
            sliderThreshold.setAttribute('data-max-h', data.max_t);
        }

        if (valThresholdEl) valThresholdEl.textContent = `t = ${data.active_t}`;
        if (valClustersEl) valClustersEl.textContent = `k = ${data.active_k} grupos`;

        if (cutLine && data.svg_tree) {
            cutLine.setAttribute('y1', data.svg_tree.cut_y);
            cutLine.setAttribute('y2', data.svg_tree.cut_y);
        }
        if (cutText && data.svg_tree) {
            cutText.setAttribute('y', data.svg_tree.cut_y - 5);
            cutText.textContent = `Corte t=${data.active_t} (k=${data.active_k})`;
        }

        if (dendroLinksGroup && data.svg_tree && data.svg_tree.links) {
            dendroLinksGroup.innerHTML = data.svg_tree.links.map(l => 
                `<path d="${l.path}" stroke="#64748b" stroke-width="1.8" class="transition-all hover:stroke-cyan-400"></path>`
            ).join('');
        }

        if (dendroLeavesGroup && data.svg_tree && data.svg_tree.leaves) {
            dendroLeavesGroup.innerHTML = data.svg_tree.leaves.map(lf =>
                `<circle cx="${lf.x}" cy="${lf.y}" r="3.5" fill="${lf.color}" stroke="#ffffff" stroke-width="1"></circle>`
            ).join('');
        }

        if (dendroLeafLabels && data.svg_tree && data.svg_tree.leaves) {
            dendroLeafLabels.innerHTML = data.svg_tree.leaves.map(lf =>
                `<span class="font-bold hover:underline cursor-pointer dendro-leaf" style="color: ${lf.color};" data-unit="${lf.name}">${lf.name}</span>`
            ).join('');
        }

        if (clustermapTbody && data.rows) {
            clustermapTbody.innerHTML = data.rows.map(r => {
                const cells = r.vals.map(val => 
                    `<td class="py-2 px-2 text-center font-mono text-[11px]" style="background-color: rgba(124, 58, 237, ${(val / 100 * 0.40).toFixed(2)}); color: ${val > 25 ? '#ffffff' : 'inherit'};">${val}%</td>`
                ).join('');
                return `
                <tr class="hover:bg-surface-container-high/60 transition-colors clustermap-unit-row" data-unit="${r.name}">
                    <td class="py-2.5 px-3 font-bold text-on-surface flex items-center gap-2 whitespace-nowrap">
                        <span class="size-2.5 rounded-full shrink-0" style="background-color: ${r.color};"></span>
                        <span>${r.name}</span>
                        <span class="text-[10px] text-outline font-normal">(${r.total_events} ev)</span>
                    </td>
                    <td class="py-2 px-2 text-center">
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold" style="background-color: ${r.color}22; color: ${r.color}; border: 1px solid ${r.color}44;">
                            ${r.group_label}
                        </span>
                    </td>
                    <td class="py-2 px-2 text-center font-mono text-[11px]">
                        <span class="px-1.5 py-0.5 rounded text-[10px] bg-surface-container-high text-on-surface-variant border border-outline-variant/30">
                            ${r.stability_pct}%
                        </span>
                    </td>
                    ${cells}
                </tr>`;
            }).join('');
        }

        if (taxonomyGroupCards && data.groups) {
            taxonomyGroupCards.innerHTML = data.groups.map(g => {
                const warnHtml = g.small_group_warning ? `
                <div class="mt-2 p-2 rounded bg-amber-500/10 border border-amber-500/30 text-amber-800 dark:text-amber-300 text-[10px] flex items-center gap-1.5">
                    <span class="material-symbols-outlined text-xs">warning</span>
                    <span>${g.small_group_warning}</span>
                </div>` : '';

                const axesHtml = g.radar_axes.slice(0, 4).map(ax => `
                <div class="flex items-center justify-between text-[11px]">
                    <span class="text-on-surface-variant truncate pr-2">${ax.category}:</span>
                    <div class="flex items-center gap-1.5 shrink-0 font-mono">
                        <span class="font-semibold text-on-surface">${ax.pct}%</span>
                        <span class="text-[10px] px-1 py-0.2 rounded bg-surface-container-high border border-outline-variant/40 ${ax.ratio >= 1.2 ? 'text-primary-container font-bold' : 'text-outline'}">
                            &times;${ax.ratio}
                        </span>
                    </div>
                </div>`).join('');

                const unitsHtml = g.units_list.map(u => 
                    `<span class="px-1.5 py-0.5 rounded bg-surface-container-high border border-outline-variant/40 text-on-surface text-[10px] font-semibold">${u}</span>`
                ).join('');

                const badgeBg = g.badge_color === 'rose' ? 'bg-rose-500/20 text-rose-600 dark:text-rose-300 border-rose-500/30' :
                                g.badge_color === 'amber' ? 'bg-amber-500/20 text-amber-700 dark:text-amber-300 border-amber-500/30' :
                                'bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border-emerald-500/30';

                return `
                <div class="rounded-xl border border-outline-variant/60 bg-surface-container p-4 shadow-sm flex flex-col justify-between space-y-3 transition-all" style="border-top: 4px solid ${g.color};">
                    <div>
                        <div class="flex items-start justify-between gap-2 mb-1.5">
                            <div class="flex items-center gap-2">
                                <span class="size-3 rounded-full shrink-0" style="background-color: ${g.color};"></span>
                                <span class="text-xs font-bold font-data-code text-on-surface">Grupo #${g.group_id}</span>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${badgeBg}">
                                ${g.alert_status}
                            </span>
                        </div>
                        <h4 class="text-sm font-bold text-on-surface font-headline-md leading-snug">
                            ${g.name}
                        </h4>
                        <p class="text-[11px] text-outline font-data-code mt-0.5 leading-relaxed">
                            ${g.rule}
                        </p>
                        ${warnHtml}
                        <div class="mt-3 pt-2 border-t border-outline-variant/30 space-y-1.5 font-data-code text-xs">
                            <span class="text-[10px] text-outline uppercase font-semibold block">Perfil composicional:</span>
                            ${axesHtml}
                        </div>
                    </div>
                    <div class="pt-2 border-t border-outline-variant/30 space-y-2 font-data-code text-[11px]">
                        <div>
                            <span class="text-outline block text-[10px] uppercase font-semibold">Unidades que integran el grupo (${g.units_count}):</span>
                            <div class="flex flex-wrap gap-1 mt-1">${unitsHtml}</div>
                        </div>
                        <div class="flex items-center justify-between text-[10px] text-outline pt-1">
                            <span>Total hechos: <strong>${g.total_events}</strong></span>
                            <span class="italic text-right max-w-[200px] truncate" title="${g.franja_info}">${g.franja_info}</span>
                        </div>
                    </div>
                </div>`;
            }).join('');
        }
    }

    linkageButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            linkageButtons.forEach(b => {
                b.classList.remove('bg-primary-container', 'text-on-primary', 'shadow-sm');
                b.classList.add('text-outline');
            });
            btn.classList.add('bg-primary-container', 'text-on-primary', 'shadow-sm');
            btn.classList.remove('text-outline');

            const linkageId = btn.getAttribute('data-linkage');
            const desc = btn.getAttribute('data-desc');
            currentLinkage = linkageId;

            if (linkageDescEl) linkageDescEl.textContent = desc;

            fetch(`/api/v1/taxonomy?ctx=${currentCtx}&linkage=${linkageId}&hellinger=true`)
                .then(r => r.json())
                .then(data => updateTaxonomyUI(data))
                .catch(err => console.error("Error al actualizar enlace taxonómico:", err));
        });
    });

    if (sliderThreshold && cutLine && cutText) {
        sliderThreshold.addEventListener('input', () => {
            const t = parseFloat(sliderThreshold.value);
            const maxH = parseFloat(sliderThreshold.getAttribute('data-max-h') || sliderThreshold.max || '1.0');
            const ySvg = Math.round(140 - (t / Math.max(0.1, maxH)) * 115);

            cutLine.setAttribute('y1', ySvg);
            cutLine.setAttribute('y2', ySvg);
            cutText.setAttribute('y', ySvg - 5);
            cutText.textContent = `Corte t=${t.toFixed(2)}`;

            if (valThresholdEl) valThresholdEl.textContent = `t = ${t.toFixed(2)}`;
        });

        sliderThreshold.addEventListener('change', () => {
            const t = parseFloat(sliderThreshold.value);
            fetch(`/api/v1/taxonomy?ctx=${currentCtx}&linkage=${currentLinkage}&t=${t}&hellinger=true`)
                .then(r => r.json())
                .then(data => updateTaxonomyUI(data))
                .catch(err => console.error("Error al recalcular corte taxonómico:", err));
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
            const branch = bg.getAttribute('data-branch');
            zoneTableRows.forEach(row => {
                row.classList.remove('bg-primary-container/20', 'border-l-4', 'border-primary-container');
            });
            const matchedBranches = document.querySelectorAll(`.dendro-branch-group[data-branch="${branch}"] path`);
            matchedBranches.forEach(p => {
                p.style.strokeWidth = '';
                p.style.filter = '';
            });
        });
    });

    // 17. Control Interactivo de la Tabla de Zonas (Búsqueda, Filtros y Ordenamiento)
    const zonesSearchInput = document.getElementById('input-zones-search');
    const filterGroupSelect = document.getElementById('select-filter-group');
    const filterAlertSelect = document.getElementById('select-filter-alert');
    const visibleCountLabel = document.getElementById('lbl-zones-visible-count');
    const tableBody = document.getElementById('zones-table-tbody');
    const sortHeaders = document.querySelectorAll('#table-zones th[data-sort-col]');

    function filterZonesTable() {
        if (!tableBody) return;
        const query = (zonesSearchInput ? zonesSearchInput.value : '').toLowerCase().trim();
        const selectedGroup = filterGroupSelect ? filterGroupSelect.value : 'todos';
        const selectedAlert = filterAlertSelect ? filterAlertSelect.value : 'todos';

        const rows = tableBody.querySelectorAll('tr.zone-row');
        let visibleCount = 0;

        rows.forEach(r => {
            const text = r.textContent.toLowerCase();
            const group = r.getAttribute('data-group-label') || '';
            const alert = r.getAttribute('data-alert') || '';

            const matchQuery = !query || text.includes(query);
            const matchGroup = (selectedGroup === 'todos') || (group === selectedGroup);
            const matchAlert = (selectedAlert === 'todos') || (alert.toLowerCase() === selectedAlert.toLowerCase());

            if (matchQuery && matchGroup && matchAlert) {
                r.classList.remove('hidden');
                visibleCount++;
            } else {
                r.classList.add('hidden');
            }
        });

        if (visibleCountLabel) {
            visibleCountLabel.textContent = visibleCount;
        }
    }

    if (zonesSearchInput) {
        zonesSearchInput.addEventListener('input', filterZonesTable);
    }
    if (filterGroupSelect) {
        filterGroupSelect.addEventListener('change', filterZonesTable);
    }
    if (filterAlertSelect) {
        filterAlertSelect.addEventListener('change', filterZonesTable);
    }

    // Ordenamiento por columnas
    let currentSortCol = null;
    let currentSortAsc = true;

    function sortTableRows(col, asc) {
        if (!tableBody) return;
        const rows = Array.from(tableBody.querySelectorAll('tr.zone-row'));

        rows.sort((a, b) => {
            let valA, valB;
            if (col === 'name') {
                valA = a.getAttribute('data-zone-name') || '';
                valB = b.getAttribute('data-zone-name') || '';
                return asc ? valA.localeCompare(valB) : valB.localeCompare(valA);
            } else if (col === 'group') {
                valA = parseInt(a.getAttribute('data-group-id') || '0', 10);
                valB = parseInt(b.getAttribute('data-group-id') || '0', 10);
                return asc ? (valA - valB) : (valB - valA);
            } else if (col === 'crime') {
                const cA = a.querySelector('td:nth-child(3) span.font-semibold');
                const cB = b.querySelector('td:nth-child(3) span.font-semibold');
                valA = cA ? cA.textContent.trim() : '';
                valB = cB ? cB.textContent.trim() : '';
                return asc ? valA.localeCompare(valB) : valB.localeCompare(valA);
            } else if (col === 'events') {
                valA = parseInt(a.getAttribute('data-events') || '0', 10);
                valB = parseInt(b.getAttribute('data-events') || '0', 10);
                return asc ? (valA - valB) : (valB - valA);
            } else if (col === 'night') {
                valA = parseFloat(a.getAttribute('data-night') || '-1');
                valB = parseFloat(b.getAttribute('data-night') || '-1');
                return asc ? (valA - valB) : (valB - valA);
            } else if (col === 'hotspots') {
                valA = parseInt(a.getAttribute('data-hotspots') || '0', 10);
                valB = parseInt(b.getAttribute('data-hotspots') || '0', 10);
                return asc ? (valA - valB) : (valB - valA);
            } else if (col === 'stability') {
                valA = parseFloat(a.getAttribute('data-stability') || '0');
                valB = parseFloat(b.getAttribute('data-stability') || '0');
                return asc ? (valA - valB) : (valB - valA);
            } else if (col === 'alert') {
                valA = a.getAttribute('data-alert') || '';
                valB = b.getAttribute('data-alert') || '';
                return asc ? valA.localeCompare(valB) : valB.localeCompare(valA);
            }
            return 0;
        });

        rows.forEach(r => tableBody.appendChild(r));
    }

    sortHeaders.forEach(th => {
        th.addEventListener('click', () => {
            const col = th.getAttribute('data-sort-col');
            if (currentSortCol === col) {
                currentSortAsc = !currentSortAsc;
            } else {
                currentSortCol = col;
                currentSortAsc = true;
            }

            sortHeaders.forEach(h => {
                h.setAttribute('aria-sort', 'none');
                const icon = h.querySelector('.sort-icon');
                if (icon) icon.textContent = 'unfold_more';
            });

            th.setAttribute('aria-sort', currentSortAsc ? 'ascending' : 'descending');
            const sortIcon = th.querySelector('.sort-icon');
            if (sortIcon) sortIcon.textContent = currentSortAsc ? 'arrow_upward' : 'arrow_downward';

            sortTableRows(col, currentSortAsc);
        });

        th.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                th.click();
            }
        });
    });

    // Selección interactiva y vinculación de filas
    const interactiveRows = document.querySelectorAll('#table-zones tr.zone-row');
    interactiveRows.forEach(row => {
        const handleSelect = () => {
            interactiveRows.forEach(r => r.classList.remove('bg-primary-container/20', 'border-l-4', 'border-primary-container'));
            row.classList.add('bg-primary-container/20', 'border-l-4', 'border-primary-container');

            // Vincular con hojas del dendrograma
            const zoneName = row.getAttribute('data-zone-name');
            const dendroLeaves = document.querySelectorAll('.dendro-leaf-item');
            dendroLeaves.forEach(leaf => {
                const label = leaf.querySelector('text');
                if (label && zoneName && label.textContent.includes(zoneName)) {
                    leaf.classList.add('scale-125', 'font-black');
                    setTimeout(() => leaf.classList.remove('scale-125', 'font-black'), 2000);
                }
            });
        };

        row.addEventListener('click', handleSelect);
        row.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleSelect();
            }
        });
    });

    // 18. Exportación de la Tabla de Zonas a CSV
    const btnExportZonesCsv = document.getElementById('btn-export-zones-csv');
    if (btnExportZonesCsv) {
        btnExportZonesCsv.addEventListener('click', () => {
            const table = document.getElementById('table-zones');
            if (!table) return;

            const rows = Array.from(table.querySelectorAll('tbody tr.zone-row'));
            const headers = [
                "codigo",
                "nombre",
                "grupo_taxonomico",
                "delito_predominante",
                "proporcion_delito_pct",
                "volumen_eventos",
                "periodo",
                "densidad_km2",
                "porcentaje_nocturno",
                "hotspots_dbscan_espaciales",
                "estabilidad_bootstrap_pct",
                "alerta_preventiva",
                "fuente_datos",
                "metodo_agrupamiento",
                "criterio_alerta",
                "criterio_hotspots",
                "nota_densidad"
            ];

            const csvRows = [headers.join(",")];

            rows.forEach(r => {
                const code = r.getAttribute('data-zone-code') || '';
                const name = r.getAttribute('data-zone-name') || '';
                const group = r.getAttribute('data-group-label') || '';
                const alert = r.getAttribute('data-alert') || '';
                const events = r.getAttribute('data-events') || '';
                const night = r.getAttribute('data-night') || '';
                const hotspots = r.getAttribute('data-hotspots') || '';
                const stability = r.getAttribute('data-stability') || '';

                const cells = r.querySelectorAll('td');
                const crimeCell = cells[2] ? cells[2].querySelector('span.font-semibold') : null;
                const crimeName = crimeCell ? crimeCell.textContent.trim() : '';
                const crimePctCell = cells[2] ? cells[2].querySelector('span.text-outline') : null;
                const crimePct = crimePctCell ? crimePctCell.textContent.replace(/[^\d.]/g, '').trim() : '';
                const period = (currentCtx === 'chicago') ? '2024–2025' : '2024–2026';
                const density = 'No disponible (sin polígono oficial)';
                const nightVal = (night === '-1' || night === '') ? 'No disponible' : `${night}%`;

                const fuente = (currentCtx === 'chicago') ? 'CPD Crimes 2024-2025 Curated Parquet' : 'Bolivia News Curated Press Corpus Gold';
                const metodo = 'Ward Agglomerative Hierarchical Clustering (Hellinger)';
                const criterioAlerta = (currentCtx === 'chicago')
                    ? 'Terciles relativos de delitos violentos (homicidio, armas, agresión y robo)'
                    : 'Sin clasificar (muestra periodística exploratoria)';
                const criterioHotspots = (currentCtx === 'chicago') ? 'DBSCAN eps codo k-distancia, MinPts=25' : 'DBSCAN eps=2500m, MinPts=2';
                const notaDensidad = 'Omitida por rigor: sin shapefile oficial de polígonos distritales en repositorio';

                const rowValues = [
                    `"${code}"`,
                    `"${name.replace(/"/g, '""')}"`,
                    `"${group}"`,
                    `"${crimeName.replace(/"/g, '""')}"`,
                    `"${crimePct}"`,
                    `"${events}"`,
                    `"${period}"`,
                    `"${density}"`,
                    `"${nightVal}"`,
                    `"${hotspots}"`,
                    `"${stability}"`,
                    `"${alert}"`,
                    `"${fuente}"`,
                    `"${metodo}"`,
                    `"${criterioAlerta}"`,
                    `"${criterioHotspots}"`,
                    `"${notaDensidad}"`
                ];
                csvRows.push(rowValues.join(","));
            });

            const csvContent = "\uFEFF" + csvRows.join("\r\n");
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `tabla_zonas_${currentCtx}_${new Date().toISOString().slice(0, 10)}.csv`;
            link.click();
            URL.revokeObjectURL(link.href);
        });
    }

    // 19. Exportación del Mapa Táctico a Imagen PNG
    const btnExportMapPng = document.getElementById('btn-export-map-png');
    if (btnExportMapPng) {
        btnExportMapPng.addEventListener('click', () => {
            const svgEl = document.getElementById('tactical-map-svg');
            if (!svgEl) return;

            const canvas = document.createElement('canvas');
            const width = 1200;
            const height = 800;
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');

            // 1. Fondo oscuro uniforme
            ctx.fillStyle = '#0b1120';
            ctx.fillRect(0, 0, width, height);

            // 2. Encabezado institucional
            ctx.fillStyle = '#1e293b';
            ctx.fillRect(20, 20, width - 40, 60);

            ctx.fillStyle = '#f8fafc';
            ctx.font = 'bold 16px "JetBrains Mono", monospace, sans-serif';
            const title = (currentCtx === 'chicago')
                ? 'MAPA TÁCTICO DE DENSIDAD CRIMINAL // CHICAGO POLICE DEPT. (2024–2025)'
                : 'MAPA TÁCTICO DE DENSIDAD CRIMINAL // BOLIVIA PRENSA NACIONAL (2024–2026)';
            ctx.fillText(title, 40, 50);

            ctx.fillStyle = '#94a3b8';
            ctx.font = '12px "JetBrains Mono", monospace, sans-serif';
            const sub = (currentCtx === 'chicago')
                ? 'Métrica esférica Haversine · DBSCAN, HDBSCAN & OPTICS · Benchmark auditado CPD'
                : 'Métrica esférica Haversine · DBSCAN, HDBSCAN & OPTICS · Corpus curado de noticias';
            ctx.fillText(sub, 40, 68);

            // 3. Serialización del SVG
            const serializer = new XMLSerializer();
            let svgStr = serializer.serializeToString(svgEl);
            if (!svgStr.includes('xmlns=')) {
                svgStr = svgStr.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"');
            }
            const svgBlob = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' });
            const url = URL.createObjectURL(svgBlob);
            const img = new Image();

            img.onload = () => {
                ctx.drawImage(img, 20, 90, width - 40, 620);
                URL.revokeObjectURL(url);

                // 4. Pie con Leyendas y Metadatos
                ctx.fillStyle = '#1e293b';
                ctx.fillRect(20, 720, width - 40, 60);

                // DBSCAN (#00e5ff)
                ctx.fillStyle = '#00e5ff';
                ctx.beginPath();
                ctx.arc(40, 750, 6, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = '#f8fafc';
                ctx.font = '11px "JetBrains Mono", monospace';
                ctx.fillText('Hotspots DBSCAN', 55, 754);

                // HDBSCAN (#10b981)
                ctx.fillStyle = '#10b981';
                ctx.beginPath();
                ctx.arc(220, 750, 6, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = '#f8fafc';
                ctx.fillText('Rescatados HDBSCAN', 235, 754);

                // OPTICS (#f59e0b)
                ctx.fillStyle = '#f59e0b';
                ctx.beginPath();
                ctx.arc(420, 750, 6, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = '#f8fafc';
                ctx.fillText('Valles OPTICS (ξ=0.05)', 435, 754);

                // Sello de Procedencia
                ctx.fillStyle = '#64748b';
                ctx.font = '10px "JetBrains Mono", monospace';
                ctx.fillText(`Exportado: ${new Date().toISOString().slice(0, 10)} · Arquitectura Medallion Gold`, 760, 754);

                // Disparo de descarga
                const link = document.createElement('a');
                link.download = `mapa_tactico_${currentCtx}_${new Date().toISOString().slice(0, 10)}.png`;
                link.href = canvas.toDataURL('image/png');
                link.click();
            };

            img.src = url;
        });
    }

    // 20. Manejo de Navegación Sticky Interna con Scroll Suave (Resumen · Mapa · Modelos · Taxonomía · Tabla · Validación)
    const navAnchors = document.querySelectorAll('nav a[href^="#"]');
    navAnchors.forEach(anchor => {
        anchor.addEventListener('click', (e) => {
            const hash = anchor.getAttribute('href');
            if (hash && hash.length > 1) {
                const target = document.querySelector(hash);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    // Si el destino es la sección de validación, asegurarse de que el acordeón esté desplegado
                    if (hash === '#validacion') {
                        const details = document.getElementById('validation-details');
                        if (details) details.open = true;
                    }
                    if (window.history && window.history.pushState) {
                        window.history.pushState(null, null, hash);
                    }
                }
            }
        });
    });
});
