import os
from modules.factory import create_app

app = create_app(os.environ.get('FLASK_ENV', 'dev'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"===========================================================")
    print(f"CPD ANALYTICS CORE // URBAN INTELLIGENCE PLATFORM (CHICAGO)")
    print(f"Iniciando servidor Flask en http://127.0.0.1:{port}")
    print(f"Modo Noche / Modo Dia: ACTIVADO (Local Storage & Auto Detect)")
    print(f"Diseño Responsivo: MOVIL, TABLETA Y DESKTOP ACTIVADOS")
    print(f"===========================================================")
    app.run(host='0.0.0.0', port=port, debug=True)
