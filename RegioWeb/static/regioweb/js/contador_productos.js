// contador_productos.js
function actualizarContadorCarrito(cantidad) {
    const contador = document.getElementById('carrito-count');
    if (contador) contador.textContent = cantidad;
}

document.querySelectorAll('.btn-agregar').forEach(btn => {
    btn.addEventListener('click', e => {
        e.preventDefault();
        const productoId = btn.dataset.producto;

        fetch(`/carrito/agregar/${productoId}/`, { method: 'POST', headers: { 'X-CSRFToken': '{{ csrf_token }}' } })
            .then(resp => resp.json())
            .then(data => {
                if (data.status === 'ok') {
                    // Sumar +1 al contador
                    const contador = document.getElementById('carrito-count');
                    if (contador) contador.textContent = parseInt(contador.textContent) + 1;
                }
            });
    });
});