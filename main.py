import os

from fastapi import FastAPI, Depends, Request, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

app = FastAPI()

# Configura la carpeta de plantillas
templates = Jinja2Templates(directory="templates")

# Configura la carpeta de archivos estáticos (imágenes)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configura la conexión a la base de datos PostgreSQL
DATABASE_URL = "postgresql://databasemenu_user:ZnoY5wh7SjJ3aybp42olfAeaR6xmzWWm@dpg-ckr9rehrfc9c73djbtu0-a/databasemenu"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Define el modelo de Producto utilizando SQLAlchemy
class ProductoModel(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    imagen = Column(String, index=True)
    nombre = Column(String, index=True)
    descripcion = Column(Text)


# Crea las tablas en la base de datos (si no existen)
Base.metadata.create_all(bind=engine)


# Modelo Pydantic para Producto
class ProductoBase(BaseModel):
    nombre: str
    descripcion: str


class ProductoCreate(ProductoBase):
    imagen: UploadFile


class ProductoUpdate(ProductoBase):
    pass


# Función para obtener una sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Página de inicio para listar productos
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    productos = db.query(ProductoModel).all()
    return templates.TemplateResponse("index.html", {"request": request, "productos": productos})


# Página para crear un nuevo producto
@app.get("/crear_producto", response_class=HTMLResponse)
async def create_product_page(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})


# Crear un nuevo producto
@app.post("/crear_producto", response_class=JSONResponse)
async def create_product(producto: ProductoCreate, db: Session = Depends(get_db)):
    # Verifica si la imagen ya existe
    if os.path.exists(f"static/{producto.imagen.filename}"):
        raise HTTPException(status_code=400, detail="La imagen ya existe")

    # Guarda la imagen en el sistema de archivos
    with open(f"static/{producto.imagen.filename}", "wb") as file:
        file.write(producto.imagen.file.read())

    db_product = ProductoModel(
        imagen=producto.imagen.filename,
        nombre=producto.nombre,
        descripcion=producto.descripcion
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return JSONResponse(content={"message": "Producto creado exitosamente"})


# Ver un producto por su ID
@app.get("/ver_producto/{id}", response_class=HTMLResponse)
async def read_product(request: Request, id: int, db: Session = Depends(get_db)):
    producto = db.query(ProductoModel).filter(ProductoModel.id == id).first()
    if producto:
        return templates.TemplateResponse("read.html", {"request": request, "producto": producto})
    raise HTTPException(status_code=404, detail="Producto no encontrado")


# Página para actualizar un producto por su ID
@app.get("/actualizar_producto/{id}", response_class=HTMLResponse)
async def update_product_page(request: Request, id: int, db: Session = Depends(get_db)):
    producto = db.query(ProductoModel).filter(ProductoModel.id == id).first()
    if producto:
        return templates.TemplateResponse("update.html", {"request": request, "producto": producto})
    raise HTTPException(status_code=404, detail="Producto no encontrado")


# Actualizar un producto por su ID
@app.put("/actualizar_producto/{id}", response_class=JSONResponse)
async def update_product(id: int, producto: ProductoUpdate, db: Session = Depends(get_db)):
    db_product = db.query(ProductoModel).filter(ProductoModel.id == id).first()
    if db_product:
        if producto.nombre is not None:
            db_product.nombre = producto.nombre
        if producto.descripcion is not None:
            db_product.descripcion = producto.descripcion
        db.commit()
        db.refresh(db_product)
        return JSONResponse(content={"message": "Producto actualizado exitosamente"})
    raise HTTPException(status_code=404, detail="Producto no encontrado")


# Página para eliminar un producto por su ID
@app.get("/eliminar_producto/{id}", response_class=HTMLResponse)
async def delete_product_page(request: Request, id: int, db: Session = Depends(get_db)):
    producto = db.query(ProductoModel).filter(ProductoModel.id == id).first()
    if producto:
        return templates.TemplateResponse("delete.html", {"request": request, "producto": producto})
    raise HTTPException(status_code=404, detail="Producto no encontrado")


# Eliminar un producto por su ID
@app.delete("/eliminar_producto/{id}", response_class=JSONResponse)
async def delete_product(id: int, db: Session = Depends(get_db)):
    db_product = db.query(ProductoModel).filter(ProductoModel.id == id).first()
    if db_product:
        # Elimina la imagen del sistema de archivos
        imagen_path = os.path.join("static", str(db_product.imagen))
        if os.path.exists(imagen_path):
            os.remove(imagen_path)
        db.delete(db_product)
        db.commit()
        return JSONResponse(content={"message": "Producto eliminado exitosamente"})
    raise


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000)
