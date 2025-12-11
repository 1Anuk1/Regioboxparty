// contacto.js
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('formContacto');
    const alertContainer = document.getElementById('alertErrores');
    const modalEl = document.getElementById('modalContacto');
    const modal = (modalEl && typeof bootstrap !== 'undefined') ? new bootstrap.Modal(modalEl) : null;
    const modalIcon = document.getElementById('modalIcon');
    const modalTitulo = document.getElementById('modalTitulo');
    const modalMensaje = document.getElementById('modalMensaje');
    const submitBtn = form?.querySelector('[type="submit"]');
    const urlEnviar = form?.dataset?.url;

    const getCookie = name => {
        const match = document.cookie.match(new RegExp('(^|; )' + name + '=([^;]*)'));
        return match ? decodeURIComponent(match[2]) : null;
    };
    const csrftoken = getCookie('csrftoken');

    const limpiarAlertas = () => alertContainer.innerHTML = '';

    const mostrarAlertas = errores => {
        limpiarAlertas();
        alertContainer.innerHTML = `<div class="alert alert-danger alert-dismissible fade show" role="alert">
                                    <strong>Errores:</strong>
                                    <ul class="mb-0">${errores.map(e => `<li>${e}</li>`).join('')}</ul>
                                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
                                </div>`;
        alertContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    };

    const setBtnDisabled = (v = true) => {
        if (!submitBtn) return;
        submitBtn.disabled = v;
        submitBtn.classList.toggle('opacity-75', v);
    };

    const mostrarModal = (titulo, mensaje, tipo = 'info') => {
        if (!modal) return alert(`${titulo}\n\n${mensaje}`);
        if (modalTitulo) modalTitulo.textContent = titulo;
        if (modalMensaje) modalMensaje.innerHTML = mensaje;

        // Cambiar ícono según el tipo
        if (modalIcon) {
            let icono = 'info';
            let color = '#5cb6ebff';
            if (tipo === 'ok') { icono = 'check_circle'; color = '#5bdd61';
            } else if (tipo === 'error') { icono = 'cancel'; color = '#dc3545';
            } else if (tipo === 'warning') { icono = 'warning'; color = '#ffc107';
            }
            modalIcon.textContent = icono;
            modalIcon.style.color = color;
        }
        modal.show();
    };

    form.addEventListener('submit', async e => {
        e.preventDefault();
        limpiarAlertas();
        setBtnDisabled(true);
        const formData = new FormData(form);

        try {
            const res = await fetch(urlEnviar, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken, 'X-Requested-With': 'XMLHttpRequest' },
                body: formData,
                credentials: 'same-origin'
            });

            const ct = res.headers.get('content-type') || '';
            if (!ct.includes('application/json')) throw new Error('Respuesta inválida del servidor');

            const data = await res.json();
            if (!data || !data.status) throw new Error('Formato de respuesta inesperado');

            if (data.status === 'validation_error') {
                mostrarAlertas(Array.isArray(data.errors) ? data.errors : ['Hay errores en el formulario.']);
            } else if (data.status === 'ok') {
                mostrarModal('¡Mensaje enviado!', data.message || 'Nos pondremos en contacto contigo pronto.', 'ok');
                form.reset();
            } else if (data.status === 'error') {
                mostrarModal('Error al enviar', data.message || 'Ocurrió un problema al enviar el mensaje. Intenta más tarde.', 'error');
            } else {
                mostrarModal('Error', 'Respuesta inesperada del servidor.', 'warning');
            }
        } catch (err) {
            mostrarModal('Error al enviar', 'Ocurrió un error inesperado. Intenta más tarde.', 'error');
        } finally {
            setBtnDisabled(false);
        }
    });
});
