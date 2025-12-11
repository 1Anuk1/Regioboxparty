// sidebar.js
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('toggleBtn');
    const header = document.querySelector('.header');
    const mainContent = document.getElementById('contenidoPrincipal');
    const menuLinks = document.querySelectorAll('#menu a');
    const logoutLinks = document.querySelectorAll('.logout-link, .dropdown-item.text-danger');

    function esMovil() {
        return window.innerWidth < 992;
    }

    function ajustarSidebar() {
        if (esMovil()) {
            // Móvil cerrado por defecto
            sidebar.classList.remove('colapsado');
            sidebar.classList.remove('movil-abierto');
            sidebar.classList.add('movil-cerrado');
            header.classList.remove('expandido');
            mainContent.classList.remove('expandido');
            document.body.classList.remove('sidebar-abierto');
        } else {
            // Escritorio: quitar clases móviles
            sidebar.classList.remove('movil-cerrado', 'movil-abierto');
            document.body.classList.remove('sidebar-abierto');
        }
    }

    // Toggle del sidebar
    toggleBtn.addEventListener('click', () => {
        if (esMovil()) {
            const abierto = sidebar.classList.toggle('movil-abierto');
            sidebar.classList.toggle('movil-cerrado', !abierto);
            document.body.classList.toggle('sidebar-abierto', abierto);
        } else {
            sidebar.classList.toggle('colapsado');
            header.classList.toggle('expandido');
            mainContent.classList.toggle('expandido');
        }
    });

    // Cerrar sidebar móvil al hacer click en links
    [...menuLinks, ...logoutLinks].forEach(link => {
        link.addEventListener('click', () => {
            if (esMovil()) {
                sidebar.classList.remove('movil-abierto');
                sidebar.classList.add('movil-cerrado');
                document.body.classList.remove('sidebar-abierto');
            }
        });
    });

    // Cerrar sidebar móvil al hacer click fuera
    document.addEventListener('click', (e) => {
        if (esMovil()) {
            const sidebarAbierto = sidebar.classList.contains('movil-abierto');
            if (sidebarAbierto && !sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                sidebar.classList.remove('movil-abierto');
                sidebar.classList.add('movil-cerrado');
                document.body.classList.remove('sidebar-abierto');
            }
        }
    });

    window.addEventListener('resize', ajustarSidebar);
    ajustarSidebar();
});
