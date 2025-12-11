document.addEventListener("DOMContentLoaded", () => {
    // Inicializamos todos los modales de Bootstrap
    const editarModal = new bootstrap.Modal(document.getElementById('editarCategoriaModal'));
    const eliminarModal = new bootstrap.Modal(document.getElementById('eliminarModal'));
    const reactivarModal = new bootstrap.Modal(document.getElementById('reactivarCategoriaModal'));
    const accionModal = new bootstrap.Modal(document.getElementById('accionModal'));

    // Elementos del formulario de editar categoría
    const editarForm = document.getElementById('formEditarCategoria');
    const inputId = document.getElementById('editar_idCategoria');
    const inputNombre = document.getElementById('editar_nombre');
    const erroresContainer = document.getElementById('editarErrores');
    const erroresList = document.getElementById('editarErroresList');

    // Botones de confirmación
    const eliminarConfirmBtn = document.getElementById('eliminarConfirmBtn');
    const reactivarConfirmBtn = document.getElementById('reactivarConfirmBtn');

    // Variables para guardar el formulario o categoría en uso
    let formSeleccionado = null;
    let reactivarTargetId = null;
    const CATEGORIAS_URL = document.getElementById('formCategoria').getAttribute('action');
    const PRODUCTOS_URL = document.getElementById('formProducto').getAttribute('action');

    // Función para obtener la cookie CSRF, necesaria para POST en Django
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            document.cookie.split(';').some(cookie => {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
                    return true;
                }
            });
        }
        return cookieValue;
    }

    // Función para mostrar errores en el modal de editar
    function showErrors(arr) {
        if (!erroresContainer || !erroresList) { alert(arr.join('\n')); return; }
        erroresList.innerHTML = '';
        arr.forEach(msg => { const li = document.createElement('li'); li.textContent = msg; erroresList.appendChild(li); });
        erroresContainer.classList.remove('d-none');
    }

    function clearErrors() {
        if (!erroresContainer || !erroresList) return;
        erroresList.innerHTML = '';
        erroresContainer.classList.add('d-none');
    }

    // Función para mostrar el modal de "acción completada"
    function mostrarModalAccion({ title = 'Acción completada', message = 'La acción se ha realizado correctamente.', icon = 'fas fa-check-double' } = {}) {
        document.getElementById('accionTitulo').textContent = title;
        document.getElementById('accionMensaje').textContent = message;
        document.getElementById('accionIcon').className = icon;

        accionModal.show();
    }

    // EDITAR CATEGORÍA
    document.body.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-editar-cat');
        if (!btn) return;
        inputId.value = btn.dataset.id || '';
        inputNombre.value = btn.dataset.nombre || '';
        clearErrors();
        editarModal.show();
    });

    editarForm?.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        clearErrors();
        const formData = new FormData(editarForm);

        try {
            const res = await fetch(CATEGORIAS_URL, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            });
            const data = await res.json();

            if (!res.ok && data.conflict_inactive) {
                // mostrar modal de reactivación
                reactivarTargetId = data.id;
                document.getElementById('reactivarMensaje').textContent = data.message;
                reactivarModal.show();
                return;
            }

            if (res.ok && data.success) {
                editarModal.hide();
                const id = formData.get('idCategoria');
                const updatedName = data.nombre || formData.get('nombre');
                const btn = document.querySelector(`.btn-editar-cat[data-id="${id}"]`);
                if (btn) {
                    const li = btn.closest('li');
                    li.querySelector('span').textContent = updatedName;
                    btn.dataset.nombre = updatedName;
                }
                mostrarModalAccion({ title: 'Categoría Actualizada', message: data.message || 'Categoría editada correctamente.' });
            } else {
                showErrors(data.errors || [data.message || 'Error desconocido.']);
            }
        } catch {
            showErrors(['Error de red.']);
        }
    });

    // ELIMINAR CATEGORÍA
    document.body.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-eliminar-cat');
        if (!btn) return;
        formSeleccionado = btn.closest('form');
        document.getElementById('eliminarMensaje').innerHTML = '¿Estás seguro que deseas <u>eliminar</u> esta categoría?';
        eliminarModal.show();
    });

    eliminarConfirmBtn?.addEventListener('click', async () => {
        if (!formSeleccionado) return;
        const fd = new FormData(formSeleccionado);
        fd.set('tipo', 'eliminar_categoria');
        try {
            const res = await fetch(CATEGORIAS_URL, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCookie('csrftoken') },
                body: fd
            });
            const data = await res.json();
            if (res.ok && data.success) {
                const li = formSeleccionado.closest('li');
                if (li) li.remove();
                eliminarModal.hide();
                formSeleccionado = null;
                window.location.reload();
            } else {
                alert(data.errors?.join('\n') || 'Error desconocido.');
            }
        } catch {
            alert('Error de red.');
        }
    });

    // REACTIVAR CATEGORÍA
    reactivarConfirmBtn?.addEventListener('click', async () => {
        if (!reactivarTargetId) return;
        const fd = new FormData();
        fd.append('tipo', 'reactivar_categoria');
        fd.append('idCategoria', reactivarTargetId);

        try {
            const res = await fetch(CATEGORIAS_URL, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCookie('csrftoken') },
                body: fd
            });
            const data = await res.json();
            if (res.ok && data.success) {
                const li = document.querySelector(`.form-eliminar-cat input[value="${data.idCategoria}"]`)?.closest('li');
                if (li) {
                    li.querySelector('span').textContent = data.nombre;
                    li.style.display = '';
                }
                reactivarModal.hide();
                editarModal.hide();
                reactivarTargetId = null;
                window.location.reload();
            } else {
                alert(data.errors?.join('\n') || 'Error desconocido.');
            }
        } catch {
            alert('Error de red.');
        }
    });

    // FLAG de creación/edición via backend
    const guardarFlagsEl = document.getElementById('guardadoFlags');
    if (guardarFlagsEl) {
        const categoriaGuardada = guardarFlagsEl.dataset.categoriaGuardada === "True";
        const mensajeGuardado = guardarFlagsEl.dataset.mensajeGuardado || '';
        const tipo = guardarFlagsEl.dataset.tipo || 'crear';
        if (categoriaGuardada) {
            mostrarModalAccion({
                title: tipo === 'editar' ? 'Categoría Actualizada' : 'Categoría Guardada',
                message: mensajeGuardado
            });
            if (window.history.replaceState) window.history.replaceState(null, null, window.location.href);
        }
    }

    // PRODUCTOS
    const productoForm = document.getElementById('formProducto');
    const erroresProdContainer = document.querySelector('#collapseProductos .alert-danger');
    const erroresProdList = erroresProdContainer ? erroresProdContainer.querySelector('ul') : null;

    function showProductErrors(arr) {
        if (!erroresProdContainer || !erroresProdList) { alert(arr.join('\n')); return; }
        erroresProdList.innerHTML = '';
        arr.forEach(msg => {
            const li = document.createElement('li');
            li.textContent = msg;
            erroresProdList.appendChild(li);
        });
        erroresProdContainer.classList.remove('d-none');
    }

    function clearProductErrors() {
        if (!erroresProdContainer || !erroresProdList) return;
        erroresProdList.innerHTML = '';
        erroresProdContainer.classList.add('d-none');
    }

    productoForm?.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        clearProductErrors();
        const formData = new FormData(productoForm);

        try {
            const res = await fetch(productoForm.getAttribute('action'), {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            });
            const data = await res.json();

            if (res.ok && data.success) {
                mostrarModalAccion({
                    title: 'Producto Guardado',
                    message: data.message || 'El producto se guardó correctamente.'
                });
            } else {
                showProductErrors(data.errors || [data.message || 'Error desconocido.']);
            }
        } catch {
            showProductErrors(['Error de red.']);
        }
    });

    document.getElementById('accionModal').addEventListener('hidden.bs.modal', () => {
        window.location.reload();
    });

    // EDITAR PRODUCTO
    const editarProductoModal = new bootstrap.Modal(document.getElementById('editarProductoModal'));
    const editarFormProducto = document.getElementById('formEditarProducto');
    const erroresContainerProd = document.getElementById('editarErroresProd');
    const erroresListProd = document.getElementById('editarErroresListProd');

    function showErrorsProd(arr) {
        if (!erroresContainerProd || !erroresListProd) { alert(arr.join('\n')); return; }
        erroresListProd.innerHTML = '';
        arr.forEach(msg => {
            const li = document.createElement('li');
            li.textContent = msg;
            erroresListProd.appendChild(li);
        });
        erroresContainerProd.classList.remove('d-none');
    }

    function clearErrorsProd() {
        if (!erroresContainerProd || !erroresListProd) return;
        erroresListProd.innerHTML = '';
        erroresContainerProd.classList.add('d-none');
    }

    // Abrir modal y llenar campos - ACTUALIZADO PARA idProducto STRING
    document.body.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-editar-prod');
        if (!btn) return;

        // Campos actualizados para idProducto string
        document.getElementById('editar_idProducto').value = btn.dataset.id;
        document.getElementById('editar_prodIdProducto').value = btn.dataset.idproducto || ''; // Nuevo campo para ID string
        document.getElementById('editar_prodNombre').value = btn.dataset.nombre;
        document.getElementById('editar_prodDescripcion').value = btn.dataset.descripcion;
        document.getElementById('editar_prodPrecio').value = btn.dataset.precio;
        document.getElementById('editar_prodPublicado').checked = btn.dataset.activo === "True";

        // Categoría
        const selectCat = document.getElementById('editar_prodCategoria');
        const catValue = btn.dataset.categoria || '';

        if (selectCat) {
            // Si la categoría existe entre las opciones, la selecciona
            if (catValue && selectCat.querySelector(`option[value="${CSS.escape ? CSS.escape(catValue) : catValue}"]`)) {
                selectCat.value = catValue;
            } else {
                // Si no existe (categoría inactiva), deja el select en la opción por defecto
                selectCat.value = '';
            }
        }

        clearErrorsProd();
        editarProductoModal.show();
    });

    editarFormProducto?.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        clearErrorsProd();
        const formData = new FormData(editarFormProducto);

        try {
            const res = await fetch(editarFormProducto.getAttribute('action'), {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            });
            const data = await res.json();

            if (res.ok && data.success) {
                editarProductoModal.hide();
                mostrarModalAccion({
                    title: 'Producto Actualizado',
                    message: data.message || 'El producto se actualizó correctamente.'
                });
            } else {
                showErrorsProd(data.errors || [data.message || 'Error desconocido.']);
            }
        } catch {
            showErrorsProd(['Error de red.']);
        }
    });

    let formSeleccionadoProd = null;

    // ACTIVAR/INACTIVAR
    document.body.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-accion-prod');
        if (!btn) return;

        e.preventDefault(); // Evitar envío del form

        formSeleccionadoProd = btn.closest('form');
        const estado = btn.dataset.activo === "True" ? "eliminar" : "activar";
        document.getElementById('eliminarMensaje').innerHTML = `¿Estás seguro que deseas <u>${estado}</u> este producto?`;
        eliminarModal.show();
    });

    // Confirmar acción desde el modal
    eliminarConfirmBtn?.addEventListener('click', async () => {
        if (!formSeleccionadoProd) return;

        const fd = new FormData(formSeleccionadoProd);
        fd.set('tipo', 'cambiar_estado_producto');

        try {
            const res = await fetch(PRODUCTOS_URL, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: fd
            });

            const data = await res.json();

            if (res.ok && data.success) {
                // Ocultar modal
                eliminarModal.hide();

                // Actualizar botón y badge
                const btn = formSeleccionadoProd.querySelector('.btn-accion-prod');
                if (btn) {
                    btn.dataset.activo = data.activo ? "True" : "False";

                    // Cambiar icono y clase
                    if (data.activo) {
                        btn.classList.remove('btn-success');
                        btn.classList.add('btn-danger');
                        btn.innerHTML = '<i class="fas fa-eraser"></i>';
                    } else {
                        btn.classList.remove('btn-danger');
                        btn.classList.add('btn-success');
                        btn.innerHTML = '<i class="fas fa-check-double"></i>';
                    }
                }

                // Actualizar badge de estado
                const badge = formSeleccionadoProd.closest('.card-body').querySelector('.badge');
                if (badge) {
                    badge.textContent = data.activo ? 'PUBLICADO' : 'NO PUBLICADO';

                    // Cambiar clases
                    badge.classList.remove('bg-activo', 'bg-inactivo');
                    badge.classList.add(data.activo ? 'bg-activo' : 'bg-inactivo');
                }

                formSeleccionadoProd = null;
            } else {
                // Oculta el modal de confirmación si aún está visible
                if (typeof eliminarModal !== 'undefined') {
                    eliminarModal.hide();
                }

                mostrarModalAccion({
                    title: 'No se pudo completar la acción',
                    message: data.errors?.join('\n') || data.message || 'Error desconocido.',
                    icon: 'fas fa-exclamation-triangle text-danger'
                });
            }
        } catch {
            alert('Error de red.');
        }
    });

    // BUSCADOR
    (() => {
        const buscador = document.getElementById('buscadorProductos');
        if (!buscador) return;

        buscador.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();

                const texto = this.value.trim();
                const url = new URL(window.location.href);

                if (texto) {
                    url.searchParams.set('search', texto);
                } else {
                    url.searchParams.delete('search');
                }
                url.searchParams.set('page', '1');

                window.location.href = url.toString();
            }
        });

        const buscadorIcon = document.querySelector('.buscador-icon');
        if (buscadorIcon) {
            buscadorIcon.addEventListener('click', () => {
                const texto = buscador.value.trim();
                const url = new URL(window.location.href);

                if (texto) {
                    url.searchParams.set('search', texto);
                } else {
                    url.searchParams.delete('search');
                }
                url.searchParams.set('page', '1');
                window.location.href = url.toString();
            });
        }
    })();

});