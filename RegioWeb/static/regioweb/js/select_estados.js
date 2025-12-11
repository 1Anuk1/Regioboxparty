// select_estados.js
$(document).ready(function(){
    function llenarEstados(idEstadoSelect, idCiudadSelect, ciudadActual = null, estadoActual = null) {
        let estadosHTML = "<option value='' disabled selected>Selecciona el estado</option>";
        for (let key in municipios) {
            if (municipios.hasOwnProperty(key)) {
                estadosHTML += `<option value="${key}">${key}</option>`;
            }
        }
        $(`#${idEstadoSelect}`).html(estadosHTML);

        if (estadoActual) $(`#${idEstadoSelect}`).val(estadoActual);

        actualizarMunicipios(idEstadoSelect, idCiudadSelect, ciudadActual);

        $(`#${idEstadoSelect}`).change(function(){
            actualizarMunicipios(idEstadoSelect, idCiudadSelect);
        });
    }

    function actualizarMunicipios(idEstadoSelect, idCiudadSelect, ciudadActual = null) {
        let estado = $(`#${idEstadoSelect}`).val();
        let html = "<option value='' disabled selected>Selecciona el municipio</option>";
        if (estado && municipios[estado]) {
            municipios[estado].forEach(mun => {
                html += `<option value="${mun}">${mun}</option>`;
            });
        }
        $(`#${idCiudadSelect}`).html(html);
        if (ciudadActual) $(`#${idCiudadSelect}`).val(ciudadActual);
    }

    // Inicializar modal Agregar
    llenarEstados('agregar_estado', 'agregar_ciudad');

    // Inicializar modal Editar cuando se abra
    $('#modalEditarDireccion').on('show.bs.modal', function(e){
        const boton = e.relatedTarget;
        const estado = boton.getAttribute('data-estado');
        const ciudad = boton.getAttribute('data-ciudad');

        llenarEstados('editar_estado', 'editar_ciudad', ciudad, estado);
    });
});