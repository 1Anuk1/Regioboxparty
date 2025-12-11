// cotizaciones.js
document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 Iniciando script de cotizaciones...');

    // Verificar que Bootstrap está disponible
    if (typeof bootstrap === 'undefined') {
        console.error('❌ Bootstrap no está disponible');
        return;
    }

    // PRODUCTOS - FORMULARIO CREACIÓN
    const tipoEntrega = document.getElementById('tipoEntrega');
    const camposDomicilio = document.getElementById('camposDomicilio');

    console.log('🏠 Elementos de domicilio:', {
        tipoEntrega: !!tipoEntrega,
        camposDomicilio: !!camposDomicilio
    });

    function toggleDomicilio() {
        if (!camposDomicilio) return;
        camposDomicilio.style.display = tipoEntrega.value === 'domicilio' ? 'block' : 'none';
        console.log('🏠 Cambiando visibilidad domicilio:', camposDomicilio.style.display);
    }

    if (tipoEntrega) {
        tipoEntrega.addEventListener('change', toggleDomicilio);
        toggleDomicilio(); // Estado inicial
    }

    const productosContainer = document.getElementById('productosContainer');
    console.log('📦 Contenedor productos creación:', !!productosContainer);

    // Agregar producto - CREACIÓN
    const agregarProductoBtn = document.getElementById('agregarProducto');
    if (agregarProductoBtn) {
        agregarProductoBtn.addEventListener('click', function () {
            console.log('➕ Agregando producto en creación');
            if (!productosContainer) return;

            const fila = productosContainer.querySelector('.productoFila').cloneNode(true);
            fila.querySelector('select').selectedIndex = 0;
            fila.querySelector('input[name="cantidad"]').value = '';
            productosContainer.appendChild(fila);
            console.log('✅ Producto agregado en creación');
        });
    }

    // Quitar producto - CREACIÓN
    if (productosContainer) {
        productosContainer.addEventListener('click', function (e) {
            if (e.target.classList.contains('btnEliminar')) {
                console.log('➖ Eliminando producto en creación');
                if (productosContainer.querySelectorAll('.productoFila').length > 1) {
                    e.target.closest('.productoFila').remove();
                    console.log('✅ Producto eliminado en creación');
                } else {
                    console.log('⚠️ No se puede eliminar el último producto');
                }
            }
        });
    }

    // BUSCADOR
    const input = document.getElementById('buscadorCotizaciones');
    const tabla = document.getElementById('tablaCotizaciones');
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
            const cliente = (fila.cells[1]?.textContent || '').toLowerCase();
            const tipo = (fila.cells[3]?.textContent || '').toLowerCase();
            const origen = (fila.cells[5]?.textContent || '').toLowerCase();
            const estado = (fila.cells[6]?.textContent || '').toLowerCase();

            const coincide = !filtro || cliente.includes(filtro) || tipo.includes(filtro) || origen.includes(filtro) || estado.includes(filtro);
            fila.style.display = coincide ? '' : 'none';
            if (coincide) visibles++;
        });

        msg.style.display = visibles ? 'none' : 'block';
    });

    // MODAL DE EDICIÓN - Inicialización segura
    console.log('🎯 Inicializando modales...');

    const editarModalEl = document.getElementById('editarModal');
    const editarForm = document.getElementById('editarForm');
    const alertContainer = document.getElementById('editarAlertContainer');
    const btnGuardarEdicion = document.getElementById('btnGuardarEdicion');
    const editarTipoEntrega = document.getElementById('editarTipoEntrega');
    const editarCamposDomicilio = document.getElementById('editarCamposDomicilio');
    const editarProductosContainer = document.getElementById('editarProductosContainer');
    const editarAgregarProducto = document.getElementById('editarAgregarProducto');

    console.log('📝 Elementos modal edición:', {
        editarModalEl: !!editarModalEl,
        editarForm: !!editarForm,
        alertContainer: !!alertContainer,
        btnGuardarEdicion: !!btnGuardarEdicion,
        editarTipoEntrega: !!editarTipoEntrega,
        editarCamposDomicilio: !!editarCamposDomicilio,
        editarProductosContainer: !!editarProductosContainer,
        editarAgregarProducto: !!editarAgregarProducto
    });

    // Inicializar modales solo si existen
    let editarModal = null;
    if (editarModalEl) {
        try {
            editarModal = new bootstrap.Modal(editarModalEl);
            console.log('✅ Modal de edición inicializado');
        } catch (error) {
            console.error('❌ Error inicializando modal de edición:', error);
        }
    }

    // Función para mostrar alertas
    function mostrarAlerta(mensaje, tipo = 'danger', timeout = 3000) {
        console.log(`💬 Mostrando alerta: ${mensaje}`, { tipo, timeout });

        if (!alertContainer) {
            console.error('❌ Contenedor de alertas no encontrado');
            alert(Array.isArray(mensaje) ? mensaje.join('\n') : mensaje);
            return;
        }

        let contenido = mensaje;

        if (tipo === 'danger' && Array.isArray(mensaje)) {
            contenido = `<strong>Errores:</strong><ul class="mb-0">${mensaje.map(e => `<li>${e}</li>`).join('')}</ul>`;
        }

        alertContainer.innerHTML = `<div class="alert alert-${tipo} alert-dismissible" role="alert">${contenido} 
                                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;

        if (timeout > 0) {
            setTimeout(() => {
                const alertEl = alertContainer.querySelector('.alert');
                if (alertEl) alertEl.remove();
                console.log('🧹 Alerta removida');
            }, timeout);
        }
    }

    // Función para crear una fila de producto editable
    function crearFilaProductoEditar(producto = null, index = 0) {
        const productoId = producto ? producto.id : '';
        const productoNombre = producto ? producto.nombre : '';
        const cantidad = producto ? producto.cantidad : '';

        console.log(`📝 Creando fila producto editable:`, { productoId, productoNombre, cantidad, index });

        return `
            <div class="productoFilaEditar mb-2 d-flex gap-1 align-items-center" data-producto-id="${productoId}">
                <select name="producto_editar" class="form-select producto-select-editar" required>
                    <option value="">Selecciona un producto</option>
                </select>
                <input type="number" name="cantidad_editar" min="1" placeholder="Cantidad" 
                       class="form-control" value="${cantidad}" required>
                <button type="button" class="btn btn-sm btn-danger btnEliminarEditar">X</button>
            </div>
        `;
    }

    // Función para cargar productos SOLO en selects vacíos
    function cargarProductosEnSelects() {
        console.log('🔄 Cargando productos en selects vacíos...');

        if (!editarProductosContainer) {
            console.error('❌ Contenedor de productos no encontrado');
            return;
        }

        const selects = editarProductosContainer.querySelectorAll('.producto-select-editar');
        console.log(`🔍 Encontrados ${selects.length} selects`);

        selects.forEach((select, index) => {
            console.log(`📝 Procesando select ${index + 1}`, {
                optionsCount: select.children.length,
                hasOptions: select.children.length > 1
            });

            // SOLO cargar productos si el select está vacío (solo tiene la opción por defecto)
            if (select.children.length <= 1) {
                console.log(`➕ Cargando productos en select vacío ${index + 1}`);

                // Agregar options desde los productos disponibles
                if (window.productosDisponibles) {
                    console.log(`➕ Agregando ${window.productosDisponibles.length} productos al select`);

                    window.productosDisponibles.forEach(producto => {
                        const option = document.createElement('option');
                        option.value = producto.id;
                        option.textContent = producto.nombre;
                        select.appendChild(option);
                    });

                    // Si este select tiene un producto pre-seleccionado, marcarlo
                    const currentValue = select.closest('.productoFilaEditar').getAttribute('data-producto-id');
                    if (currentValue) {
                        select.value = currentValue;
                        console.log(`✅ Producto pre-seleccionado: ${currentValue}`);
                    }
                } else {
                    console.warn('⚠️ No hay productos disponibles cargados');
                }
            } else {
                console.log(`⏭️ Select ${index + 1} ya tiene productos, omitiendo`);
            }
        });
    }

    // Función para mostrar productos en el modal (editables)
    function mostrarProductosEnModal(productos) {
        console.log('📦 Mostrando productos en modal:', productos);

        if (!editarProductosContainer) {
            console.error('❌ Contenedor de productos no encontrado');
            return;
        }

        let html = '';

        if (productos.length === 0) {
            // Fila vacía por defecto
            console.log('📝 Creando fila vacía por defecto');
            html = crearFilaProductoEditar();
        } else {
            console.log(`📝 Creando ${productos.length} filas de productos`);
            productos.forEach((producto, index) => {
                html += crearFilaProductoEditar(producto, index);
            });
        }

        editarProductosContainer.innerHTML = html;
        console.log('✅ Productos cargados en modal');
        cargarProductosEnSelects();
    }

    // Función para agregar producto en edición
    function agregarProductoEditar() {
        console.log('➕ Agregando producto en edición');

        if (!editarProductosContainer) {
            console.error('❌ Contenedor de productos no encontrado');
            return;
        }

        const fila = crearFilaProductoEditar();
        editarProductosContainer.insertAdjacentHTML('beforeend', fila);
        console.log('✅ Producto agregado en edición');

        // Cargar productos SOLO en el nuevo select (los demás mantienen sus valores)
        const nuevosSelects = editarProductosContainer.querySelectorAll('.producto-select-editar');
        const ultimoSelect = nuevosSelects[nuevosSelects.length - 1];

        if (ultimoSelect && window.productosDisponibles) {
            console.log('➕ Cargando productos en el NUEVO select');
            window.productosDisponibles.forEach(producto => {
                const option = document.createElement('option');
                option.value = producto.id;
                option.textContent = producto.nombre;
                ultimoSelect.appendChild(option);
            });
        }
    }

    // Función para eliminar producto en edición
    function eliminarProductoEditar(button) {
        console.log('➖ Eliminando producto en edición');

        if (!editarProductosContainer) {
            console.error('❌ Contenedor de productos no encontrado');
            return;
        }

        const filas = editarProductosContainer.querySelectorAll('.productoFilaEditar');
        console.log(`📊 Filas actuales: ${filas.length}`);

        if (filas.length > 1) {
            button.closest('.productoFilaEditar').remove();
            console.log('✅ Producto eliminado en edición');
        } else {
            console.log('⚠️ No se puede eliminar el último producto');
            mostrarAlerta('No se puede eliminar el último producto.', 'warning', 2000);
        }
    }

    // Event listeners para productos editables
    if (editarAgregarProducto) {
        editarAgregarProducto.addEventListener('click', agregarProductoEditar);
        console.log('✅ Listener agregado para botón añadir producto');
    }

    if (editarProductosContainer) {
        // Eliminar producto (delegación de eventos)
        editarProductosContainer.addEventListener('click', function (e) {
            if (e.target.classList.contains('btnEliminarEditar')) {
                eliminarProductoEditar(e.target);
            }
        });
        console.log('✅ Listener agregado para eliminar productos');
    }

    // Manejar cambio de tipo de entrega en edición
    if (editarTipoEntrega && editarCamposDomicilio) {
        editarTipoEntrega.addEventListener('change', function () {
            console.log('🏠 Cambiando tipo entrega en edición:', this.value);
            if (this.value === 'domicilio') {
                editarCamposDomicilio.style.display = 'block';
            } else {
                editarCamposDomicilio.style.display = 'none';
            }
        });
        console.log('✅ Listener agregado para cambio de tipo entrega');
    }

    // Función para obtener productos disponibles - CON MEJOR MANEJO DE ERRORES
    function obtenerProductosDisponibles() {
        console.log('🌐 Solicitando productos disponibles...');
        return fetch('/regiocrm/productos-disponibles/', {
            method: 'GET',
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                console.log('📨 Respuesta productos disponibles:', response.status);
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    window.productosDisponibles = data.productos;
                    console.log(`✅ ${data.productos.length} productos disponibles cargados`);
                    return data.productos;
                } else {
                    console.error('❌ Error cargando productos disponibles:', data.error);
                    return [];
                }
            })
            .catch(error => {
                console.error('🌐 Error de red obteniendo productos:', error);
                // RETORNAR ARRAY VACÍO PARA QUE CONTINÚE EL PROCESO
                return [];
            });
    }

    // Función para cargar productos de la cotización - CON MEJOR MANEJO DE ERRORES
    function cargarProductosCotizacion(cotizacionId) {
        console.log(`🌐 Cargando productos de cotización ${cotizacionId}...`);

        if (!editarProductosContainer) {
            console.error('❌ Contenedor de productos no encontrado');
            return;
        }

        // Mostrar loading
        editarProductosContainer.innerHTML = '<div class="text-center py-3"><div class="spinner-border spinner-border-sm" role="status"></div> Cargando productos...</div>';

        // Usar Promise.allSettled para que continúe aunque falle alguna petición
        Promise.allSettled([
            obtenerProductosDisponibles(),
            fetch(`/regiocrm/cotizaciones/${cotizacionId}/productos/`, {
                method: 'GET',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            }).then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP error! status: ${res.status}`);
                }
                console.log('📨 Respuesta productos cotización:', res.status);
                return res.json();
            }).catch(error => {
                console.error('🌐 Error cargando productos de cotización:', error);
                return { success: false, error: error.message };
            })
        ])
            .then(([resultDisponibles, resultCotizacion]) => {
                console.log('📊 Resultados de promesas:', {
                    disponibles: resultDisponibles.status,
                    cotizacion: resultCotizacion.status
                });

                const productosDisponibles = resultDisponibles.status === 'fulfilled' ? resultDisponibles.value : [];
                const dataCotizacion = resultCotizacion.status === 'fulfilled' ? resultCotizacion.value : { success: false, productos: [] };

                if (dataCotizacion.success) {
                    console.log(`✅ ${dataCotizacion.productos.length} productos de cotización cargados`);
                    mostrarProductosEnModal(dataCotizacion.productos);
                } else {
                    console.error('❌ Error cargando productos de cotización');
                    // MOSTRAR PRODUCTOS VACÍOS PERO PERMITIR CONTINUAR
                    mostrarProductosEnModal([]);
                }
            })
            .catch(error => {
                console.error('🌐 Error inesperado cargando productos:', error);
                // MOSTRAR PRODUCTOS VACÍOS PERO PERMITIR CONTINUAR
                mostrarProductosEnModal([]);
            });
    }

    // Abrir modal con datos de la cotización
    if (editarModalEl) {
        editarModalEl.addEventListener('show.bs.modal', function (event) {
            console.log('🎯 Abriendo modal de edición');
            const button = event.relatedTarget;

            if (!button) {
                console.error('❌ Botón relacionado no encontrado');
                return;
            }

            // Obtener datos de los atributos data-
            const cotizacionId = button.getAttribute('data-id');
            const cliente = button.getAttribute('data-cliente');
            const fecha = button.getAttribute('data-fecha');
            const tipoEntrega = button.getAttribute('data-tipo-entrega');
            const calle = button.getAttribute('data-calle');
            const numero = button.getAttribute('data-numero');
            const colonia = button.getAttribute('data-colonia');
            const estadoDomicilio = button.getAttribute('data-estado');
            const ciudad = button.getAttribute('data-ciudad');
            const codigoPostal = button.getAttribute('data-codigo-postal');
            const estadoCotizacion = button.getAttribute('data-estado-cotizacion');
            const comentarios = button.getAttribute('data-comentarios');

            console.log('📝 Datos del botón:', {
                cotizacionId, cliente, fecha, tipoEntrega, estadoCotizacion
            });

            // Llenar el formulario
            document.getElementById('editarCotizacionId').value = cotizacionId;
            document.getElementById('editarCliente').value = cliente;
            document.getElementById('editarFecha').value = fecha;
            document.getElementById('editarTipoEntrega').value = tipoEntrega;
            document.getElementById('editarCalle').value = calle;
            document.getElementById('editarNumero').value = numero;
            document.getElementById('editarColonia').value = colonia;
            document.getElementById('editar_estado').value = estadoDomicilio;
            document.getElementById('editar_ciudad').value = ciudad;
            document.getElementById('editarCodigoPostal').value = codigoPostal;
            document.getElementById('editarEstadoCotizacion').value = estadoCotizacion;
            document.getElementById('editarComentarios').value = comentarios;

            // Cargar productos de la cotización
            cargarProductosCotizacion(cotizacionId);

            // Manejar campos de domicilio
            if (tipoEntrega === 'domicilio') {
                editarCamposDomicilio.style.display = 'block';
            } else {
                editarCamposDomicilio.style.display = 'none';
            }

            // Limpiar alertas previas
            if (alertContainer) {
                alertContainer.innerHTML = '';
            }

            console.log('✅ Modal de edición configurado');
        });
    }

    // También limpiar productos cuando se cierra el modal
    if (editarModalEl) {
        editarModalEl.addEventListener('hidden.bs.modal', function () {
            console.log('🔒 Modal de edición cerrado');
            if (editarProductosContainer) {
                editarProductosContainer.innerHTML = '';
                console.log('🧹 Productos limpiados');
            }
        });
    }

    // Función para consolidar productos duplicados
    function consolidarProductosDuplicados(productosEditar, cantidadesEditar) {
        console.log('🔄 Consolidando productos duplicados...');

        const productosConsolidados = new Map();

        // Agrupar productos por ID y sumar cantidades
        productosEditar.forEach((select, index) => {
            if (select.value && cantidadesEditar[index].value) {
                const productoId = select.value;
                const cantidad = parseInt(cantidadesEditar[index].value) || 0;

                if (productosConsolidados.has(productoId)) {
                    // Si ya existe, sumar la cantidad
                    productosConsolidados.set(productoId, productosConsolidados.get(productoId) + cantidad);
                    console.log(`➕ Sumando cantidad para producto ${productoId}: +${cantidad}`);
                } else {
                    // Si no existe, agregar nuevo
                    productosConsolidados.set(productoId, cantidad);
                    console.log(`🆕 Agregando producto ${productoId} con cantidad: ${cantidad}`);
                }
            }
        });

        // Convertir Map a arrays separados
        const productosUnicos = Array.from(productosConsolidados.keys());
        const cantidadesConsolidadas = Array.from(productosConsolidados.values());

        console.log('📊 Productos consolidados:', {
            productosUnicos,
            cantidadesConsolidadas,
            totalProductos: productosUnicos.length
        });

        return { productosUnicos, cantidadesConsolidadas };
    }

    // Guardar cambios con productos editables - CON PREVENCIÓN DE REFRESH
    if (btnGuardarEdicion) {
        btnGuardarEdicion.addEventListener('click', function (event) {
            console.log('💾 Guardando cambios...');

            // PREVENIR EL COMPORTAMIENTO POR DEFECTO
            event.preventDefault();
            event.stopPropagation();

            console.log('🔍 DEBUG - Evento prevenido, página NO debería recargarse');

            if (!editarForm) {
                console.error('❌ Formulario de edición no encontrado');
                return;
            }

            const formData = new FormData(editarForm);

            // Agregar flag de edición
            formData.append('editar_cotizacion', 'true');

            // Agregar productos editables al FormData
            const productosEditar = editarProductosContainer.querySelectorAll('select[name="producto_editar"]');
            const cantidadesEditar = editarProductosContainer.querySelectorAll('input[name="cantidad_editar"]');

            console.log(`📦 Procesando ${productosEditar.length} productos antes de consolidar`);

            console.log('🔍 ANTES de consolidar - Productos:', Array.from(productosEditar).map(s => s.value));
            console.log('🔍 ANTES de consolidar - Cantidades:', Array.from(cantidadesEditar).map(i => i.value));

            const { productosUnicos, cantidadesConsolidadas } = consolidarProductosDuplicados(productosEditar, cantidadesEditar);

            console.log('🔍 DESPUÉS de consolidar - Productos únicos:', productosUnicos);
            console.log('🔍 DESPUÉS de consolidar - Cantidades consolidadas:', cantidadesConsolidadas);

            // Validar que haya al menos un producto después de consolidar
            if (productosUnicos.length === 0) {
                console.warn('⚠️ No hay productos válidos después de consolidar');
                mostrarAlerta(['Debe agregar al menos un producto válido.'], 'danger', 0);
                return;
            }

            // LIMPIAR productos existentes del FormData antes de agregar los consolidados
            formData.delete('producto_editar');
            formData.delete('cantidad_editar');

            // Agregar productos consolidados al FormData
            productosUnicos.forEach(productoId => {
                formData.append('producto_editar', productoId);
            });

            cantidadesConsolidadas.forEach(cantidad => {
                formData.append('cantidad_editar', cantidad.toString());
            });

            console.log('📊 Productos a guardar (consolidados):', {
                productos: productosUnicos,
                cantidades: cantidadesConsolidadas
            });

            // Mostrar loading en el botón
            const originalText = btnGuardarEdicion.innerHTML;
            btnGuardarEdicion.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
            btnGuardarEdicion.disabled = true;

            console.log('🌐 Enviando datos al servidor...');
            // JUSTO ANTES del fetch, agrega:
            console.log('🔍 DEBUG - FormData completo:');
            for (let [key, value] of formData.entries()) {
                console.log(`   ${key}: ${value}`);
            }

            console.log('🌐 Enviando datos al servidor...');
            fetch(window.location.href, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: formData
            })
                .then(res => {
                    console.log('📨 Respuesta del servidor:', res.status);
                    return res.json();
                })
                .then(data => {
                    console.log('📊 Datos de respuesta:', data);

                    if (data.success) {
                        console.log('✅ Cambios guardados exitosamente');
                        mostrarAlerta(data.mensaje || 'Cambios guardados correctamente.', 'success', 1000);
                        setTimeout(() => {
                            if (editarModal) {
                                editarModal.hide();
                                console.log('🔒 Modal cerrado');
                            }
                            window.location.reload();
                        }, 1000);
                    } else {
                        console.error('❌ Error guardando cambios:', data.errores);
                        const errores = data.errores || ['Error inesperado'];
                        mostrarAlerta(errores, 'danger', 0);
                    }
                })
                .catch(err => {
                    console.error('🌐 Error de red:', err);
                    mostrarAlerta('Error inesperado al guardar los cambios.', 'danger', 3000);
                })
                .finally(() => {
                    // Restaurar botón
                    btnGuardarEdicion.innerHTML = originalText;
                    btnGuardarEdicion.disabled = false;
                    console.log('🔄 Botón restaurado');
                });
        });
    }

    console.log('🎉 Script de cotizaciones completamente inicializado');
});