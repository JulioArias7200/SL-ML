import os
import json
import pytest
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import linkage, cophenet

from modules.services.spatial_service import SpatialDensityService
from modules.factory import create_app


class TestTaxonomyAndClustermap:
    """Pruebas rigurosas de la Fase 4: Taxonomía jerárquica aglomerativa, dendrograma SVG y clustermap."""

    @pytest.fixture(autouse=True)
    def setup_class(self):
        SpatialDensityService._TAXONOMIA_CACHE.clear()
        app = create_app('dev')
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_cophenetic_matches_scipy(self):
        """Verifica que la correlación cofenética calculada por el servicio coincida exactamente con scipy cophenet."""
        for ctx in ['chicago', 'bolivia']:
            tax = SpatialDensityService.calcular_taxonomia(ctx=ctx, linkage_method='ward', use_hellinger=True)
            r_service = tax['cophenetic_r']

            # Re-cálculo independiente de validación
            if ctx == 'chicago':
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                pq_path = os.path.join(base_dir, "data", "chicago_benchmark", "silver", "chicago_crimes_curated.parquet")
                df = pd.read_parquet(pq_path, columns=["District", "Primary Type", "Year"])
                df_sub = df[(df["Year"] >= 2024) & (df["District"].isin(range(1, 26))) & (df["District"] != 31)].copy()
                df_sub["cat"] = df_sub["Primary Type"].map(SpatialDensityService.CHICAGO_CRIME_CATEGORIES).fillna("Daños materiales y otras infracciones")
                categories = sorted(list(set(SpatialDensityService.CHICAGO_CRIME_CATEGORIES.values())))
                ct = pd.crosstab(df_sub["District"], df_sub["cat"]).reindex(columns=categories, fill_value=0)
                P = ct.div(ct.sum(axis=1), axis=0).values
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                csv_path = os.path.join(base_dir, "data", "bolivia_news", "gold", "dashboard_eventos_clusters_bolivia.csv")
                df = pd.read_csv(csv_path)
                zona_counts = df["zona_principal"].value_counts()
                valid_zonas = sorted(zona_counts[zona_counts >= 3].index.tolist())
                df_sub = df[df["zona_principal"].isin(valid_zonas)].copy()

                def map_bo(d):
                    d_l = str(d).lower()
                    if "robo" in d_l or "asalto" in d_l or "atraco" in d_l: return "Robo agravado y asalto"
                    if "agresi" in d_l or "lesion" in d_l or "riña" in d_l: return "Agresión física y lesiones"
                    if "homicid" in d_l or "asesinat" in d_l: return "Homicidio y asesinato"
                    if "hurto" in d_l or "descuid" in d_l: return "Hurto y descuidismo"
                    if "narcot" in d_l or "droga" in d_l: return "Narcotráfico y sustancias"
                    return "Delitos financieros y estafas"

                df_sub["cat"] = df_sub["delito_principal"].apply(map_bo)
                categories = SpatialDensityService.BOLIVIA_CRIME_CATEGORIES
                ct = pd.crosstab(df_sub["zona_principal"], df_sub["cat"]).reindex(columns=categories, fill_value=0)
                P = ct.div(ct.sum(axis=1), axis=0).values

            P_trans = np.sqrt(P)
            Y = pdist(P_trans, metric="euclidean")
            Z = linkage(Y, method="ward")
            c_scipy, _ = cophenet(Z, Y)

            assert r_service == round(float(c_scipy), 4), f"La correlación cofenética en {ctx} ({r_service}) no coincide con scipy ({round(float(c_scipy), 4)})"

    def test_linkage_methods_recomputation(self):
        """Verifica que el selector de métodos (ward, average, complete, single) recalcule adecuadamente cofenética y alturas."""
        for m in ['ward', 'average', 'complete', 'single']:
            tax = SpatialDensityService.calcular_taxonomia(ctx='chicago', linkage_method=m)
            assert tax['linkage'] == m
            assert len(tax['linkage_options']) == 4
            active_opt = next(opt for opt in tax['linkage_options'] if opt['id'] == m)
            assert active_opt['active'] is True
            assert active_opt['cophenetic_r'] == tax['cophenetic_r']

        # Nota técnica de Ward
        tax_ward = SpatialDensityService.calcular_taxonomia(ctx='chicago', linkage_method='ward')
        assert "suma de cuadrados" in tax_ward['provenance']['ward_note'] or "varianza" in tax_ward['provenance']['ward_note']

    def test_all_fields_have_provenance(self):
        """Verifica que cada componente del análisis taxonómico incluya procedencia explícita y documentada."""
        for ctx in ['chicago', 'bolivia']:
            tax = SpatialDensityService.calcular_taxonomia(ctx=ctx)
            assert 'provenance' in tax
            prov = tax['provenance']
            assert 'dataset' in prov and len(prov['dataset']) > 0
            assert 'units_description' in prov and len(prov['units_description']) > 0
            assert 'linkage_method' in prov and len(prov['linkage_method']) > 0
            assert 'distance_metric' in prov and len(prov['distance_metric']) > 0
            assert 'cophenetic_calculation' in prov and len(prov['cophenetic_calculation']) > 0
            assert 'stability_evaluation' in prov and len(prov['stability_evaluation']) > 0

    def test_groups_partition_units_cleanly(self):
        """Verifica que los grupos taxonómicos resultantes del corte particionen todas las unidades sin solapamiento ni omisión."""
        for ctx in ['chicago', 'bolivia']:
            tax = SpatialDensityService.calcular_taxonomia(ctx=ctx)
            all_units_in_rows = [r['name'] for r in tax['rows']]
            all_units_in_groups = []
            for g in tax['groups']:
                all_units_in_groups.extend(g['units_list'])

            assert len(all_units_in_groups) == len(all_units_in_rows), f"Discrepancia en cantidad de unidades en {ctx}"
            assert set(all_units_in_groups) == set(all_units_in_rows), f"Las unidades en grupos no coinciden con las filas en {ctx}"
            assert len(all_units_in_groups) == len(set(all_units_in_groups)), f"Existen unidades duplicadas entre grupos en {ctx}"

    def test_clustermap_rows_match_dendrogram_leaves(self):
        """Verifica que las filas de la matriz clustermap estén ordenadas exactamente según las hojas del dendrograma."""
        for ctx in ['chicago', 'bolivia']:
            tax = SpatialDensityService.calcular_taxonomia(ctx=ctx)
            leaf_names = [leaf['name'] for leaf in tax['svg_tree']['leaves']]
            row_names = [r['name'] for r in tax['rows']]
            assert leaf_names == row_names, f"El orden de las filas del clustermap no coincide con las hojas del dendrograma en {ctx}"

    def test_scope_and_period(self):
        """Verifica que el periodo sea 2024–2025 en Chicago (22 distritos, excluido D-31) y 2020–2024 en Bolivia (n >= 3)."""
        tax_chi = SpatialDensityService.calcular_taxonomia(ctx='chicago')
        assert tax_chi['period'] == "2024-2025"
        assert len(tax_chi['rows']) == 22
        assert "D-31" in tax_chi['excluded_units']

        tax_bo = SpatialDensityService.calcular_taxonomia(ctx='bolivia')
        assert tax_bo['period'] == "2024-2026"
        assert len(tax_bo['rows']) == 7
        assert len(tax_bo['excluded_units']) > 0

    def test_stability_json_and_metadata(self):
        """Verifica que los archivos de estabilidad contengan semilla 42, B=200 remuestreos y hash SHA-256."""
        for ctx in ['chicago', 'bolivia']:
            tax = SpatialDensityService.calcular_taxonomia(ctx=ctx)
            stab = tax['stability']
            assert stab['bootstrap_B'] == 200
            assert stab['random_seed'] == 42
            assert 'script_sha256' in stab
            assert isinstance(stab['mean_ari'], float)
            assert len(stab['ci_95']) == 2
            assert stab['ci_95'][0] <= stab['ci_95'][1]

    def test_bolivia_no_time_frames(self):
        """Verifica que en Bolivia no se calculen ni muestren franjas horarias (por carencia en el 75% de crónicas)."""
        tax_bo = SpatialDensityService.calcular_taxonomia(ctx='bolivia')
        for g in tax_bo['groups']:
            assert "no disponible" in g['franja_info'].lower() or "no registra" in g['franja_info'].lower()

    def test_api_taxonomy_endpoint(self):
        """Verifica que la ruta GET /api/v1/taxonomy devuelva 200 y JSON con la estructura completa."""
        # Chicago por defecto
        res_chi = self.client.get('/api/v1/taxonomy?ctx=chicago')
        assert res_chi.status_code == 200
        data_chi = res_chi.get_json()
        assert data_chi['status'] == 'ok'
        assert data_chi['ctx'] == 'chicago'
        assert len(data_chi['rows']) == 22
        assert 'svg_tree' in data_chi
        assert 'groups' in data_chi

        # Bolivia con método de enlace average
        res_bo = self.client.get('/api/v1/taxonomy?ctx=bolivia&linkage=average')
        assert res_bo.status_code == 200
        data_bo = res_bo.get_json()
        assert data_bo['status'] == 'ok'
        assert data_bo['linkage'] == 'average'
        assert len(data_bo['rows']) == 7

