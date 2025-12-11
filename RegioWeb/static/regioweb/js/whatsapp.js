// whatsapp.js
document.addEventListener('DOMContentLoaded', () => {
    const btnWhatsapp = document.getElementById('btnWhatsapp');
    const popup = document.getElementById('whatsappPopup');
    const closePopup = document.getElementById('closePopup');
    const enviarBtn = document.getElementById('enviarWhatsapp');

    btnWhatsapp.addEventListener('click', () => {
        popup.style.display = (popup.style.display === 'flex') ? 'none' : 'flex';
    });

    closePopup.addEventListener('click', () => {
        popup.style.display = 'none';
    });

    enviarBtn.addEventListener('click', () => {
        const mensaje = encodeURIComponent(document.getElementById('mensajeWhatsapp').value);
        const numero = '5218110025264';
        if (mensaje.trim() !== '') {
            window.open(`https://wa.me/${numero}?text=${mensaje}`, '_blank');
        }
    });
});
