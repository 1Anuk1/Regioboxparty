// inicio.js
(function () {
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const c = cookies[i].trim();
        if (c.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(c.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  const csrftoken = getCookie('csrftoken');

  // URL del carrito
  const CART_URL = '/carrito/';

  // Mostrar modal y recargar al cerrarlo
  function showConfirmModalAndReload() {
    const modalEl = document.getElementById('modalConfirmacion');
    if (!modalEl) {
      window.location.reload();
      return;
    }

    // Si ya existe una instancia anterior, la quitamos para asegurar listeners limpios
    if (modalEl._bsModalInstance) {
      try { modalEl._bsModalInstance.hide(); } catch (e) {}
      modalEl._bsModalInstance = null;
    }

    const bsModal = new bootstrap.Modal(modalEl);
    modalEl._bsModalInstance = bsModal;

    // Cuando el modal se oculta se recarga la página
    const onHidden = function () {
      modalEl.removeEventListener('hidden.bs.modal', onHidden);
      window.location.reload();
    };
    modalEl.addEventListener('hidden.bs.modal', onHidden);

    // configurar botón "Ir al carrito"
    const btnIr = document.getElementById('btnIrCarrito');
    if (btnIr) {
      btnIr.setAttribute('href', CART_URL);
    }
    bsModal.show();
  }

  // Delegado de clicks para botones de añadir
  document.addEventListener('click', async function (e) {
    const btn = e.target.closest('.btn-agregar');
    if (!btn) return;

    const productoId = btn.dataset.id;
    if (!productoId) return;

    try {
      btn.disabled = true;

      const resp = await fetch(`/carrito/agregar/${productoId}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': csrftoken,
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        },
        body: new URLSearchParams({})
      });

      if (!resp.ok) {
        // error, recargar para que se muestre mensaje server-side
        window.location.reload();
        return;
      }

      // éxito, mostrar modal y recargar cuando se cierre
      showConfirmModalAndReload();

    } catch (err) {
      console.error('Error al agregar al carrito:', err);
      window.location.reload();
    } finally {
      btn.disabled = false;
    }
  });
})();