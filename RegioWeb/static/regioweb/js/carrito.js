// carrito.js
// Leer csrftoken desde cookie (Django)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i=0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length+1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length+1));
                break;
            }
        }
    }
    return cookieValue;
}
const CSRF_TOKEN = getCookie('csrftoken');

// Controles de cantidad por producto
document.querySelectorAll('.def-number-input').forEach(container => {
    const input = container.querySelector('.cantidad');
    const productoId = container.dataset.producto;

    container.querySelector('.btn-menos').addEventListener('click', () => {
        if (+input.value > +input.min) {
            input.stepDown();
            actualizarCantidad(productoId, input.value);
        }
    });

    container.querySelector('.btn-mas').addEventListener('click', () => {
        input.stepUp();
        actualizarCantidad(productoId, input.value);
    });

    input.addEventListener('change', () => {
        if (+input.value < +input.min) input.value = input.min;
        actualizarCantidad(productoId, input.value);
    });
});

function actualizarCantidad(productoId, cantidad) {
    fetch(urlActualizarCarrito.replace('/0/0/', `/${productoId}/${cantidad}/`), {
        method: 'POST',
        headers: {
            'X-CSRFToken': CSRF_TOKEN,
            'Accept': 'application/json'
        }
    }).then(resp => {
        if (!resp.ok) console.warn('Error al actualizar cantidad');
        return resp.json().catch(()=>{});
    }).then(data => {
        location.reload();
    });
}

// Mostrar/ocultar dirección según tipo de entrega
document.getElementById('tipo_entrega')?.addEventListener('change', function(){
    const direccionesDiv = document.getElementById('direccion-envio');
    if (this.value === 'domicilio') direccionesDiv.classList.remove('d-none');
    else direccionesDiv.classList.add('d-none');
});

document.addEventListener('DOMContentLoaded', function() {
    const formVaciar = document.getElementById('formVaciarCarrito');
    const btnConfirmar = document.getElementById('btnConfirmarVaciar');

    btnConfirmar.addEventListener('click', function() {
        // Envía el form manualmente
        formVaciar.submit();
    });
});