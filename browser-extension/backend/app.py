from fastapi import FastAPI, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from markitdown import MarkItDown
import tempfile
import os
import traceback
import contextlib
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configuración desde .env
EXTENSION_ID_CHROME = os.getenv("EXTENSION_ID_CHROME", "")
EXTENSION_ID_EDGE = os.getenv("EXTENSION_ID_EDGE", "")
EXTENSION_ID_FIREFOX = os.getenv("EXTENSION_ID_FIREFOX", "")
SECRET_TOKEN    = os.getenv("MIDDLEWARE_SECRET", "token-por-defecto")
TAMANO_MAXIMO   = 20 * 1024 * 1024  # 20 MB
TIPOS_PERMITIDOS = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx'}

# CORS: solo acepta peticiones de tu extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"chrome-extension://{EXTENSION_ID_CHROME}",
        f"chrome-extension://{EXTENSION_ID_EDGE}",
        f"moz-extension://{EXTENSION_ID_FIREFOX}",
    ],
    allow_methods=["POST"],
    allow_headers=["*"],
)

md = MarkItDown()

@app.post("/convertir")
async def convertir(
    archivo: UploadFile = File(...),
    x_token: str = Header(...)        # espera el header X-Token
):
    # 1. Verificar token secreto
    if x_token != SECRET_TOKEN:
        return JSONResponse(status_code=401, content={'ok': False, 'error': 'No autorizado'})

    # 2. Sanitizar nombre y validar extensión
    nombre = os.path.basename(archivo.filename)
    extension = os.path.splitext(nombre)[1].lower()

    if extension not in TIPOS_PERMITIDOS:
        return JSONResponse(status_code=400, content={'ok': False, 'error': f'Tipo "{extension}" no permitido'})

    # 3. Leer y validar tamaño
    contenido = await archivo.read()
    if len(contenido) > TAMANO_MAXIMO:
        return JSONResponse(status_code=400, content={'ok': False, 'error': 'Archivo supera el límite de 20 MB'})

    # 4. Guardar temporal, convertir y borrar garantizado
    with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
        tmp.write(contenido)
        ruta_tmp = tmp.name

    try:
        resultado = md.convert(ruta_tmp)
        markdown_texto = resultado.text_content
        return JSONResponse({'ok': True, 'markdown': markdown_texto, 'nombre_original': nombre})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'ok': False, 'error': str(e), 'detalle': traceback.format_exc()}
        )
    finally:
        with contextlib.suppress(Exception):
            os.unlink(ruta_tmp)  # siempre se borra, pase lo que pase