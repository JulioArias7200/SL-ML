"""
===============================================================================
run_bolivia_scraper.py  -  Script de ejecución del motor de ingesta Bolivia
===============================================================================
USO:
    python run_bolivia_scraper.py                      # Todos los medios + YouTube
    python run_bolivia_scraper.py --solo-web           # Solo medios web (sin YouTube)
    python run_bolivia_scraper.py --solo-yt            # Solo YouTube RSS
    python run_bolivia_scraper.py --prueba             # Solo 3 medios (modo prueba rápida)
    python run_bolivia_scraper.py --medios reduno atb  # Solo los medios indicados

Después de correrlo, inicia el servidor web para ver los resultados:
    python app.py   →   http://127.0.0.1:5000/?ctx=bolivia
===============================================================================
"""

import sys
import os
import argparse

# Reconfigurar stdout/stderr para evitar fallos de codificacion en Windows (cp1252)
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# Asegurar que el directorio raíz del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def verificar_dependencias():
    """Verifica que las dependencias mínimas estén instaladas."""
    faltantes = []
    for paquete in ["requests", "requests_cache", "pandas", "numpy", "sklearn"]:
        try:
            __import__(paquete)
        except ImportError:
            faltantes.append(paquete if paquete != "sklearn" else "scikit-learn")

    if faltantes:
        print("=" * 60)
        print("  [!] DEPENDENCIAS FALTANTES")
        print("=" * 60)
        print("  Instala las siguientes librerias antes de ejecutar:")
        print(f"  pip install {' '.join(faltantes)}")
        print()
        print("  Tambien se recomienda (mejora extraccion de texto):")
        print("  pip install trafilatura beautifulsoup4 lxml")
        print("=" * 60)
        sys.exit(1)

    # Avisos de opcionales
    for paquete, nombre_pip in [("trafilatura", "trafilatura"), ("bs4", "beautifulsoup4")]:
        try:
            __import__(paquete)
        except ImportError:
            print(f"  [AVISO] '{nombre_pip}' no instalado (recomendado). pip install {nombre_pip}")


def main():
    parser = argparse.ArgumentParser(
        description="Motor de Ingesta Incremental - Noticias Policiales Bolivia",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python run_bolivia_scraper.py                        # Correr todo
  python run_bolivia_scraper.py --prueba               # Modo prueba (3 medios)
  python run_bolivia_scraper.py --solo-yt              # Solo YouTube RSS
  python run_bolivia_scraper.py --medios reduno eldeber lostiempos
        """,
    )
    parser.add_argument(
        "--solo-web",
        action="store_true",
        help="Procesar solo medios web (omitir YouTube)",
    )
    parser.add_argument(
        "--solo-yt",
        action="store_true",
        help="Procesar solo los canales de YouTube (omitir medios web)",
    )
    parser.add_argument(
        "--prueba",
        action="store_true",
        help="Modo prueba: solo 3 medios para verificar que todo funciona",
    )
    parser.add_argument(
        "--medios",
        nargs="+",
        default=None,
        metavar="MEDIO",
        help="Procesar solo estos medios específicos (ej: reduno atb eldeber)",
    )
    parser.add_argument(
        "--sin-yt",
        action="store_true",
        help="Alias de --solo-web",
    )

    args = parser.parse_args()

    # ─── Verificar dependencias ───────────────────────────────────────────────
    verificar_dependencias()

    # ─── Importar servicio ────────────────────────────────────────────────────
    from modules.services.bolivia_scraper_service import (
        ejecutar_ingesta_completa,
        MEDIOS,
        CANALES_YT_RSS,
    )

    # ─── Determinar configuración de ejecución ────────────────────────────────
    medios_activos = None
    youtube_activo = True

    if args.prueba:
        # Modo prueba: 3 medios populares
        medios_activos = ["reduno", "atb", "eldeber"]
        print("[PRUEBA] Modo prueba activado: solo 3 medios -> reduno, atb, eldeber")

    if args.medios:
        validos = [m for m in args.medios if m in MEDIOS]
        invalidos = [m for m in args.medios if m not in MEDIOS]
        if invalidos:
            print(f"[AVISO] Medios no reconocidos (se ignoran): {invalidos}")
            print(f"        Medios disponibles: {list(MEDIOS.keys())}")
        medios_activos = validos if validos else None

    if args.solo_web or args.sin_yt:
        youtube_activo = False

    if args.solo_yt:
        medios_activos = []  # Lista vacía = no procesar medios web
        youtube_activo = True

    # ─── Ejecutar ─────────────────────────────────────────────────────────────
    try:
        resultado = ejecutar_ingesta_completa(
            medios_activos=medios_activos,
            youtube_activo=youtube_activo,
        )

        if resultado:
            nuevas = resultado.get("nuevas_esta_corrida", 0)
            total  = resultado.get("total_acumulado", 0)
            if nuevas == 0:
                print("\n  [INFO] No se encontraron noticias nuevas en esta corrida.")
                print("     (Todas las URLs ya estaban en el historico o los medios")
                print("      no tenian noticias nuevas desde la ultima ejecucion.)")
            else:
                print(f"\n  [EXITO] {nuevas} noticias nuevas sumadas. Total acumulado: {total}")

    except KeyboardInterrupt:
        print("\n\n  [INTERRUMPIDO] El scraper fue detenido manualmente.")
        print("  Las noticias recolectadas hasta este punto YA fueron guardadas.")
        print("  Puedes volver a correrlo cuando quieras para continuar.")
    except Exception as e:
        print(f"\n  [ERROR CRITICO] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
