// catalogo.js
document.addEventListener('DOMContentLoaded', function() {
    // CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const CSRF_TOKEN = getCookie('csrftoken');

    // Buscador
    const inputBuscar = document.getElementById('buscadorProductos');
    const productos = document.querySelectorAll('.producto-card');
    const productosGrid = document.getElementById('productos-grid');
    const paginacionUl = document.getElementById('paginacion');

    // Crear un contenedor para el mensaje de "no hay productos"
    const mensajeProductos = document.createElement('div');
    mensajeProductos.className = 'text-center py-5';
    mensajeProductos.innerHTML = `<div class="d-flex flex-column align-items-center justify-content-center py-5">
                                    <i class="fas fa-box-open fa-4x text-muted mb-3"></i>
                                    <h4 class="text-muted mb-2">¡Ups! No encontramos productos</h4>
                                    <p class="text-muted">Prueba con otra búsqueda o ajusta los filtros para ver resultados.</p>
                                  </div>`;
    mensajeProductos.style.display = 'none';
    productosGrid.parentNode.insertBefore(mensajeProductos, productosGrid);

    // Filtros
    const checkboxes = document.querySelectorAll('.form-check-input');
    const itemsPorPagina = 8; // productos por página
    let paginaActual = 1;

    // Devuelve productos según filtros y búsqueda
    function obtenerProductosVisibles() {
        const texto = inputBuscar.value.toLowerCase();
        const seleccionados = Array.from(checkboxes)
            .filter(chk => chk.checked)
            .map(chk => chk.value);

        return Array.from(productos).filter(prod => {
            const nombre = prod.querySelector('.card-title').textContent.toLowerCase();
            const filtroCategoria = seleccionados.includes('todos') || seleccionados.includes(prod.dataset.category);
            const filtroTexto = nombre.includes(texto);
            return filtroCategoria && filtroTexto;
        });
    }

    // Mostrar productos de una página y actualizar paginación y mensaje
    function mostrarProductosPagina(pagina) {
        const visibles = obtenerProductosVisibles();
        productos.forEach(prod => prod.style.display = 'none'); // oculta todos primero
        visibles.slice((pagina-1)*itemsPorPagina, pagina*itemsPorPagina).forEach(prod => prod.style.display = 'block');

        paginaActual = pagina;
        mensajeProductos.style.display = visibles.length > 0 ? 'none' : 'block';
        paginacionUl.style.display = visibles.length > 0 ? 'flex' : 'none';
        renderPaginacion(visibles.length);
    }

    function renderPaginacion(totalItems) {
        const totalPaginas = Math.ceil(totalItems / itemsPorPagina);
        paginacionUl.innerHTML = '';

        for (let i = 1; i <= totalPaginas; i++) {
            const li = document.createElement('li');
            li.className = 'page-item' + (i === paginaActual ? ' active' : '');
            li.innerHTML = `<a class="page-link" href="#">${i}</a>`;
            li.addEventListener('click', e => {
                e.preventDefault();
                mostrarProductosPagina(i);
            });
            paginacionUl.appendChild(li);
        }
    }

    // Eventos búsqueda
    inputBuscar.addEventListener('input', () => mostrarProductosPagina(1));

    // Eventos filtros
    checkboxes.forEach(chk => {
        chk.addEventListener('change', () => {
            if (chk.value === 'todos' && chk.checked) {
                checkboxes.forEach(c => { if (c.value !== 'todos') c.checked = false; });
            } else if (chk.value !== 'todos' && chk.checked) {
                document.getElementById('filterTodos').checked = false;
            }

            const otrosChecked = Array.from(checkboxes).some(c => c.value !== 'todos' && c.checked);
            if (!otrosChecked) document.getElementById('filterTodos').checked = true;

            mostrarProductosPagina(1); // siempre mostrar página 1 al cambiar filtro
        });

        chk.addEventListener('click', () => { chk.blur(); });
    });

    // Inicialización al cargar
    mostrarProductosPagina(1);

    // Modal de confirmación
    const modalConfirmEl = document.getElementById('modalConfirmacion');
    const modalConfirm = new bootstrap.Modal(modalConfirmEl);
    const btnSeguir = modalConfirmEl.querySelector('#btnSeguir');
    const btnIrCarrito = modalConfirmEl.querySelector('#btnIrCarrito');
    let productoSeleccionado = null;

    document.querySelectorAll('.btn-agregar').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            productoSeleccionado = this.dataset.id;
            modalConfirm.show();
        });
    });

    // POST cuando el usuario clic en "Seguir viendo"
    btnSeguir.addEventListener('click', () => {
        if (!productoSeleccionado) return;
        fetch(`${URL_AGREGAR_CARRITO}${productoSeleccionado}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        }).then(() => {
            modalConfirm.hide();
            window.location.reload();
        });
    });

    // Redirigir al carrito (pasando por POST)
    btnIrCarrito.addEventListener('click', () => {
        if (!productoSeleccionado) return;
        fetch(`${URL_AGREGAR_CARRITO}${productoSeleccionado}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'ok') {
                window.location.href = '/carrito/';
            }
        });
    });
});

// Zoom tipo "follow" para .zoom-container
(function () {
  const FACTOR_ZOOM = 2;

  // Adjunta el comportamiento de zoom a un contenedor .zoom-container
  function adjuntarAlContenedor(contenedor) {
    if (!contenedor || contenedor._zoomAdjuntado) return;
    contenedor._zoomAdjuntado = true;

    // Obtener src: preferimos data-src, si no existe buscamos un <img> de respaldo
    let fuente = contenedor.dataset.src;
    if (!fuente) {
      const fallback = contenedor.parentElement.querySelector('.zoom-source, img');
      if (fallback) fuente = fallback.src;
    }
    if (!fuente) return;

    // Establecer fondo inicialmente (imagen completa)
    contenedor.style.backgroundImage = `url("${fuente}")`;
    contenedor.style.backgroundPosition = 'center';
    contenedor.style.backgroundSize = 'contain';

    // Precargar imagen para poder usar dimensiones si es necesario
    const imagen = new Image();
    imagen.src = fuente;
    imagen.onload = function () {
      // Mueve el fondo según la posición del cursor/touch
      function manejarMovimiento(clientX, clientY) {
        const rect = contenedor.getBoundingClientRect();

        // Coordenadas relativas dentro del contenedor
        let x = clientX - rect.left;
        let y = clientY - rect.top;
        x = Math.max(0, Math.min(x, rect.width));
        y = Math.max(0, Math.min(y, rect.height));

        // Porcentajes relativos para background-position
        const xPct = (x / rect.width) * 100;
        const yPct = (y / rect.height) * 100;

        // Calcular background-size en px (ancho visible * factor)
        const anchoBg = Math.round(rect.width * FACTOR_ZOOM);
        contenedor.style.backgroundSize = `${anchoBg}px auto`;
        contenedor.style.backgroundPosition = `${xPct}% ${yPct}%`;
      }

      // Volver al estado inicial (imagen completa)
      function reiniciar() {
        contenedor.style.backgroundPosition = 'center';
        contenedor.style.backgroundSize = 'contain';
      }

      // Eventos mouse
      contenedor.addEventListener('mousemove', function (e) {
        manejarMovimiento(e.clientX, e.clientY);
      });
      contenedor.addEventListener('mouseleave', function () {
        reiniciar();
      });

      // Eventos touch (soporte móvil)
      let touchActivo = false;
      contenedor.addEventListener('touchstart', function (ev) {
        if (!ev.touches || ev.touches.length === 0) return;
        // prevenir scroll dentro del contenedor mientras el usuario interactúa
        ev.preventDefault();
        touchActivo = true;
        const t = ev.touches[0];
        manejarMovimiento(t.clientX, t.clientY);
      }, { passive: false });

      contenedor.addEventListener('touchmove', function (ev) {
        if (!touchActivo) return;
        const t = ev.touches[0];
        manejarMovimiento(t.clientX, t.clientY);
      }, { passive: true });

      contenedor.addEventListener('touchend', function () {
        touchActivo = false;
        reiniciar();
      });
    };
  }

  // Inicializar todos los .zoom-container ya en el DOM
  function inicializarTodo() {
    document.querySelectorAll('.zoom-container').forEach(adjuntarAlContenedor);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializarTodo);
  } else {
    inicializarTodo();
  }

  // Re-adjuntar cuando cualquier modal se abra (importante para elementos ocultos)
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('shown.bs.modal', function () {
      modal.querySelectorAll('.zoom-container').forEach(adjuntarAlContenedor);
    });
    modal.addEventListener('hidden.bs.modal', function () {
      // resetear a contain al cerrar
      modal.querySelectorAll('.zoom-container').forEach(c => {
        c.style.backgroundPosition = 'center';
        c.style.backgroundSize = 'contain';
      });
    });
  });
})();

