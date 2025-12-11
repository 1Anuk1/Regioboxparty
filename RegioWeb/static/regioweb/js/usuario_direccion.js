// usuario_direccion.js
// Agregar Dirección
const modalAgregar = document.getElementById('modalAgregarDireccion');
const formAgregar = modalAgregar.querySelector('form');
const alertaAgregar = document.getElementById('agregarDireccionAlert');

formAgregar.addEventListener('submit', async e => {
    e.preventDefault();

    // Limpiamos alerta antes de mostrar nuevos mensajes
    alertaAgregar.className = 'alert d-none mx-1 mt-2';
    alertaAgregar.innerHTML = '';

    const data = new FormData(formAgregar);

    // Enviamos los datos por fetch
    const resp = await fetch(formAgregar.action, {
        method: 'POST',
        body: data,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });
    const resultado = await resp.json();

    if (resultado.ok) {
        // Éxito: mostrar mensaje, limpiar formulario, cerrar modal y recargar pestaña Direcciones
        alertaAgregar.className = 'alert alert-success mx-1 mt-2';
        alertaAgregar.textContent = resultado.msg;
        formAgregar.reset();

        setTimeout(() => {
            bootstrap.Modal.getInstance(modalAgregar).hide();
            window.location.hash = '#direcciones';
            window.location.reload();
        }, 1000);
    } else {
        // Error: mostrar lista de errores
        let errores = Array.isArray(resultado.error) ? resultado.error : [resultado.error];
        alertaAgregar.className = 'alert alert-danger mx-1 mt-2';
        alertaAgregar.innerHTML = '<strong>Errores:</strong><ul>' + errores.map(err => `<li>${err}</li>`).join('') + '</ul>';
        alertaAgregar.scrollIntoView({ behavior: 'smooth' });
    }
});

// Editar Dirección
const modalEditar = document.getElementById('modalEditarDireccion');
const formEditar = document.getElementById('formEditarDireccion');
const alertaEditar = document.getElementById('editarDireccionAlert');

// Cuando se abra el modal, rellenar campos
modalEditar.addEventListener('show.bs.modal', e => {
    const boton = e.relatedTarget;
    const id = boton.getAttribute('data-id');
    document.getElementById('editar_id_dir').value = id;

    // Rellenar inputs con los data-* del botón
    document.getElementById('editar_calle').value = boton.getAttribute('data-calle');
    document.getElementById('editar_numero').value = boton.getAttribute('data-numero');
    document.getElementById('editar_colonia').value = boton.getAttribute('data-colonia');
    document.getElementById('editar_ciudad').value = boton.getAttribute('data-ciudad');
    document.getElementById('editar_estado').value = boton.getAttribute('data-estado');
    document.getElementById('editar_codigo_postal').value = boton.getAttribute('data-cp');
    document.getElementById('principalEditar').checked = boton.getAttribute('data-principal') === 'True';

    // Actualizar acción del formulario con URL dinámica
    formEditar.action = boton.getAttribute('data-url');
});

// Envío AJAX para editar
formEditar.addEventListener('submit', async e => {
    e.preventDefault();
    alertaEditar.className = 'alert d-none mx-1 mt-2';
    alertaEditar.innerHTML = '';

    const data = new FormData(formEditar);
    const resp = await fetch(formEditar.action, {
        method: 'POST',
        body: data,
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });

    const resultado = await resp.json();

    if (resultado.ok) {
        alertaEditar.className = 'alert alert-success mx-1 mt-2';
        alertaEditar.textContent = resultado.msg;

        setTimeout(() => {
            bootstrap.Modal.getInstance(modalEditar).hide();
            window.location.hash = '#direcciones';
            window.location.reload();
        }, 1000);
    } else {
        let errores = Array.isArray(resultado.error) ? resultado.error : [resultado.error];
        alertaEditar.className = 'alert alert-danger mx-1 mt-2';
        alertaEditar.innerHTML = '<strong>Errores:</strong><ul>' + errores.map(err => `<li>${err}</li>`).join('') + '</ul>';
        alertaEditar.scrollIntoView({ behavior: 'smooth' });
    }
});

// Eliminar Dirección
const modalEliminar = document.getElementById('modalEliminarDireccion');
const formEliminar = document.getElementById('formEliminarDireccion');

modalEliminar.addEventListener('show.bs.modal', e => {
    const boton = e.relatedTarget;
    const idDireccion = boton.getAttribute('data-id');
    const urlEliminar = boton.getAttribute('data-url');

    document.getElementById('delete_id_direccion').value = idDireccion;
    formEliminar.action = urlEliminar;
});

// Activar pestaña según hash
document.addEventListener('DOMContentLoaded', () => {
    const hash = window.location.hash;
    if (hash) {
        const pestañaObjetivo = document.querySelector(`.nav-link[href="${hash}"]`);
        const panelObjetivo = document.querySelector(hash);
        if (pestañaObjetivo && panelObjetivo) {
            // Desactivar todas las pestañas
            document.querySelectorAll('.nav-link').forEach(a => a.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('show', 'active'));

            // Activar la pestaña correspondiente
            pestañaObjetivo.classList.add('active');
            panelObjetivo.classList.add('show', 'active');
        }
    }
});