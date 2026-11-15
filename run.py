from app import create_app

app = create_app()

if __name__ == "__main__":
    # host 0.0.0.0 -> acepta conexiones desde otras interfaces de red
    # debug True   -> recarga al guardar archivos (solo en desarrollo)
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=False)
