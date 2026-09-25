import models
import security
from main import SessionLocal

def create_test_user():
    db =SessionLocal()

    # Verificamos que el usuario no exista
    existing_user = db.query(models.User).filter(models.User.email == "fernandoprueba1@gmail.com").first()
    if existing_user:
        print("El usuario de prueba ya existe")
        db.close()
        return

    # Creamos el usuario con la contraseña encriptada
    test_user = models.User(
        email="fernandoprueba@gmail1.com",
        hashed_password=security.get_password_hash("Mi_contrasena_segura")
    )

    db.add(test_user)
    db.commit()
    print(f"Usuario {test_user.email} Creado con exito")
    db.close()

if __name__ == "__main__":
    create_test_user()