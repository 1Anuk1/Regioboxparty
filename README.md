# Regio Box Party

## 📌 Descripción del proyecto
Regio Box Party es una empresa que ofrece soluciones de empaques personalizados para sus clientes, principalmente del sector alimenticio.  

El proyecto consta de **dos partes principales**:

1. **RegioWeb**: Sitio web de cotizaciones tipo e-commerce, con secciones como login, registro, catálogo, carrito, contacto, FAQs, etc.  
2. **RegioCRM**: Sistema interno para la gestión de clientes y cotizaciones, accesible solo para el equipo de la empresa.  

> ⚠️ Nota: No hay pasarelas de pago; el sitio web genera cotizaciones que se gestionan internamente en el CRM.

---

## 📂 Estructura del repositorio
manage.py # Archivo principal de Django  
RegioBoxPortal/ # Proyecto Django  
RegioWeb/ # App para el sitio web  
RegioCRM/ # App para el CRM  
DB_REGIOBOX # Base de datos local  
README.md # Este archivo  

---

## ⚙️ Instalación y configuración

1. Clonar el repositorio:  
   git clone https://github.com/DevanyVargas/RegioBoxParty.git

2. Entrar al proyecto:  
   cd RegioBoxParty

3. Instalar Django (si no está instalado):  
   pip install django

4. Migrar la base de datos:  
   python manage.py makemigrations  
   python manage.py migrate  

6. Crear superusuario:  
   python manage.py createsuperuser

7. Ejecutar servidor local:  
   python manage.py runserver

---

## 🌿 Flujo de trabajo con Git

### Ramas

- **main** → Rama estable, lista para producción.  
- **feature/nombreapellido** → Ramas de desarrollo individuales para cada miembro del equipo.

Ramas del equipo:
  * feature/devanyvargas
  * feature/edgarcantu
  * feature/danielazalpa
  * feature/danielgarcia
  * feature/juanlujano

### Uso diario

1. Verifica en qué rama estás:  
   git branch  
   > ⚠️ Nota: El * indica la rama activa.

1. Cambiar a tu rama personal (si no estás en ella):  
   git checkout feature/nombreapellido

2. Traer cambios de `main` antes de empezar:  
   git checkout main  
   git pull origin main  
   git checkout feature/nombreapellido  
   git merge main  

3. Hacer cambios y subirlos a tu rama:  
   git add .  
   git commit -m "Descripción de tus cambios"  
   git push origin feature/nombre-apellido  

4. Cuando tu funcionalidad esté lista, crear un **Pull Request** a `main`.

---

## 🤝 Contribución

- Cada miembro trabaja en su **rama personal**.  
- Evitar commits directos en `main`.  
- Revisar que tu rama esté **actualizada con main** antes de mergear.  

---

## 👥 Equipo

- Devany Vargas
- Edgar Cantu diaz
- Daniela Zalpa
- Daniel García
- Juan Lujano  

---

## 📝 Notas importantes

- Mantener la estructura de Django (`manage.py`, apps, DB) intacta.  
- Las apps **RegioWeb** y **RegioCRM** tienen sus propias carpetas de `templates` y `static`.  
- Los cambios en la rama personal no afectan `main` hasta que se haga merge.  
- Usar **mensajes claros en los commits** ayuda a todos a entender los cambios.

