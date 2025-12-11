// usuario_actualizar_info.js
(function () {
    // Guardamos referencias
    var btnModificar = document.getElementById('btn-modificar');
    var vistaBox = document.getElementById('info-vista');
    var edicionBox = document.getElementById('info-edicion');
    var btnCancelar = document.getElementById('btn-cancelar');

    // Inputs
    const inpNombre = document.getElementById('input-nombre');
    const inpApellido = document.getElementById('input-apellido');
    const inpCorreo = document.getElementById('input-correo');
    const inpTelefono = document.getElementById('input-telefono');

    // Cambio de contraseña
    const chkCambiarContrasena = document.getElementById('chk-cambiar-contrasena');
    const contrasenaBloque = document.getElementById('bloque-contrasenas');
    const actContrasena = document.getElementById('contrasena-actual');
    const nuevaContrasena = document.getElementById('nueva-contrasena');
    const confirmContrasena = document.getElementById('confirmar-contrasena');

    // Guardamos originales al cargar (para restaurar si cancelan)
    const originales = {
        nombre: inpNombre ? inpNombre.value : '',
        apellido: inpApellido ? inpApellido.value : '',
        correo: inpCorreo ? inpCorreo.value : '',
        telefono: inpTelefono ? inpTelefono.value : '',
    };

    // Mostrar edición
    if (btnModificar) {
        btnModificar.addEventListener('click', function (e) {
            e.preventDefault();
            vistaBox.style.display = 'none';
            edicionBox.style.display = 'block';

            // enfocar
            if (inpNombre) inpNombre.focus();

            // restaurar inputs al abrir (asegura que siempre estén con valores originales)
            inpNombre.value = originales.nombre;
            inpApellido.value = originales.apellido;
            inpCorreo.value = originales.correo;
            inpTelefono.value = originales.telefono;

            // restaurar bloque de contraseña
            if (chkCambiarContrasena) {
                chkCambiarContrasena.checked = false;
            }
            if (contrasenaBloque) contrasenaBloque.style.display = 'none';
            if (actContrasena) actContrasena.value = '';
            if (nuevaContrasena) nuevaContrasena.value = '';
            if (confirmContrasena) confirmContrasena.value = '';
        });
    }

    // Cancelar: restaurar vista y limpiar cambios (restauramos con originales)
    if (btnCancelar) {
        btnCancelar.addEventListener('click', function (e) {
            e.preventDefault();
            edicionBox.style.display = 'none';
            vistaBox.style.display = 'block';

            // restaurar inputs (por si el usuario escribió pero canceló)
            inpNombre.value = originales.nombre;
            inpApellido.value = originales.apellido;
            inpCorreo.value = originales.correo;
            inpTelefono.value = originales.telefono;

            // limpiar contraseñas
            if (actContrasena) actContrasena.value = '';
            if (nuevaContrasena) nuevaContrasena.value = '';
            if (confirmContrasena) confirmContrasena.value = '';
            if (chkCambiarContrasena) chkCambiarContrasena.checked = false;
            if (contrasenaBloque) contrasenaBloque.style.display = 'none';
        });
    }

    // Toggle mostrar inputs de contraseña
    if (chkCambiarContrasena) {
        chkCambiarContrasena.addEventListener('change', function () {
            if (this.checked) {
                contrasenaBloque.style.display = 'flex';
            } else {
                contrasenaBloque.style.display = 'none';
                if (actContrasena) actContrasena.value = '';
                if (nuevaContrasena) nuevaContrasena.value = '';
                if (confirmContrasena) confirmContrasena.value = '';
            }
        });
    }
})();