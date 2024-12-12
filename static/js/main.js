document.addEventListener("DOMContentLoaded", function() {
    var menuToggle = document.querySelector('.menu-toggle');
    menuToggle.addEventListener('click', togglePopup);
});

function togglePopup() {
    var popup = document.getElementById("popupMenu");
    popup.classList.toggle("show");
}

$(document).ready(function() {
    $('.ui.dropdown').dropdown();
    $('.ui.rating').rating({
        interactive: true,
        maxRating: 5,
        onRate: function(value) {
            $('#starsInput').val(value); 
            console.log("Rating set to: " + value);
        }
    });
});

if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js", { scope: '/' })
        .then(() => console.log("Service Worker Registered"))
        .catch((error) => console.error("Service Worker Registration Failed:", error));
}


