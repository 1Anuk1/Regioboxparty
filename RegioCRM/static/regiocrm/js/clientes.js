// clientes.js
document.addEventListener('DOMContentLoaded', function() {
    // Buscador de clientes
    const input = document.getElementById('buscadorClientes');
    const tabla = document.getElementById('tablaClientes');
    const filas = tabla.querySelectorAll('tbody tr');

    // Crear mensaje de "no resultados"
    const msg = document.createElement('p');
    msg.textContent = 'No se encontraron resultados.';
    msg.className = 'text-center fst-italic text-muted mt-2';
    msg.style.display = 'none';
    tabla.parentElement.appendChild(msg); // lo pone debajo de la tabla

    input.addEventListener('input', function () {
        const filtro = this.value.trim().toLowerCase();
        let visibles = 0;

        filas.forEach(fila => {
            const nombre = (fila.cells[1]?.textContent || '').toLowerCase();
            const apellido = (fila.cells[2]?.textContent || '').toLowerCase();
            const correo = (fila.cells[3]?.textContent || '').toLowerCase();

            const coincide = !filtro || nombre.includes(filtro) || apellido.includes(filtro) || correo.includes(filtro);
            fila.style.display = coincide ? '' : 'none';
            if (coincide) visibles++;
        });

        msg.style.display = visibles ? 'none' : 'block';
    });

    // Modal de confirmación de cliente añadido
    const modalAdd = new bootstrap.Modal(document.getElementById('añadirModal'));
    const formAdd = document.querySelector('#accordionAddCliente form');
    const btnAdd = formAdd?.querySelector('button[type="submit"]');

    if (formAdd) {
        formAdd.addEventListener('submit', function(e) {
            e.preventDefault();

            // Deshabilitar botón solo del form de añadir cliente
            if (btnAdd) btnAdd.disabled = true;

            const formData = new FormData(formAdd);

            fetch(window.location.href, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                // Quitar alertas previas
                const erroresPrevios = formAdd.querySelector('.alert');
                if (erroresPrevios) erroresPrevios.remove();

                if (data.success) {
                    // Mostrar modal
                    modalAdd.show();
                } else {
                    // Mostrar errores dentro del acordeón
                    const alerta = document.createElement('div');
                    alerta.className = 'alert alert-danger mt-3';
                    alerta.innerHTML = `
                        <strong>Errores:</strong>
                        <ul>
                            ${data.errores.map(e => `<li>${e}</li>`).join('')}
                        </ul>
                    `;
                    formAdd.prepend(alerta);
                }
            })
            .catch(err => {
                console.error(err);
                alert('Error inesperado');
            })
            .finally(() => {
                // Volver a habilitar botón después del fetch
                if (btnAdd) btnAdd.disabled = false;
            });
        });
    }

    // Modal de edición
    const editarModal = document.getElementById('editarModal');
    const editarForm = document.getElementById('editarForm');
    const alertContainer = document.getElementById('editarAlertContainer');

    function mostrarAlerta(mensaje, tipo = 'danger', timeout = 3000) {
        let contenido = mensaje;

        // Si es tipo 'danger' y es un array, mostramos como lista con título "Errores:"
        if (tipo === 'danger' && Array.isArray(mensaje)) {
            contenido = `<strong>Errores:</strong><ul class="mb-0">${mensaje.map(e => `<li>${e}</li>`).join('')}</ul>`;
        }

        alertContainer.innerHTML = `<div class="alert alert-${tipo}" role="alert">${contenido}</div>`;

        if (timeout > 0) {
            setTimeout(() => {
                const alertEl = alertContainer.querySelector('.alert');
                if (alertEl) {
                    alertEl.remove(); // se elimina automáticamente
                }
            }, timeout);
        }
    }

    // Abrir modal con datos del cliente
    if (editarModal) {
        editarModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const clienteId = button.getAttribute('data-id');
            const nombre = button.getAttribute('data-nombre') || '';
            const apellido = button.getAttribute('data-apellido') || '';
            const correo = button.getAttribute('data-correo') || '';
            const telefono = button.getAttribute('data-telefono') || '';

            document.getElementById('editarClienteId').value = clienteId;
            document.getElementById('editarNombre').value = nombre;
            document.getElementById('editarApellido').value = apellido;
            document.getElementById('editarCorreo').value = correo;
            document.getElementById('editarTelefono').value = telefono;

            alertContainer.innerHTML = ''; // limpiar alertas previas
        });
    }

    // Envío del formulario por AJAX
    if (editarForm) {
        editarForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(editarForm);
            fetch(window.location.href, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    mostrarAlerta(data.mensaje || 'Cambios guardados correctamente.', 'success', 1500);
                    setTimeout(() => {
                        const modal = bootstrap.Modal.getInstance(editarModal);
                        modal.hide();
                        window.location.reload();
                    }, 1500);
                } else {
                    const errores = data.errores || ['Error inesperado'];
                    mostrarAlerta(errores, 'danger', 0);
                }
            })
            .catch(err => {
                mostrarAlerta('Error inesperado', 'danger', 3000);
            });
        });
    }

    // Modal de eliminar / activar
    const accionModal = document.getElementById('accionModal');
    const mensajeEl = accionModal?.querySelector('#accionMensaje');
    const btnConfirmar = accionModal?.querySelector('#accionBtn');
    let clienteId = null;
    let accion = null; // 'delete' o 'activate'

    if (accionModal) {
        accionModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            clienteId = button.getAttribute('data-id');
            accion = button.getAttribute('data-accion');
            const nombre = button.getAttribute('data-nombre') || 'este cliente';

            if (accion === 'delete') {
                mensajeEl.innerHTML = `¿Estás seguro(a) de <u>eliminar</u> a <strong>${nombre}</strong>?`;
            } else if (accion === 'activate') {
                mensajeEl.innerHTML = `¿Deseas <u>activar</u> a <strong>${nombre}</strong>?`;
            }
        });

        btnConfirmar.addEventListener('click', function() {
            if (!clienteId || !accion) return;
            const url = new URL(window.location.href);
            url.searchParams.set(accion === 'delete' ? 'delete_id' : 'activate_id', clienteId);
            window.location.href = url.toString();
        });

        accionModal.addEventListener('hidden.bs.modal', function() {
            clienteId = null;
            accion = null;
            mensajeEl.innerHTML = '¿Estás seguro de realizar esta acción?';
        });
    }
});
