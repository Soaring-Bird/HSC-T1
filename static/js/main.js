// Waits for the DOM to fully load before executing the script
document.addEventListener("DOMContentLoaded", function() {
    // Selects the menu toggle button and attaches a click event listener to it
    var menuToggle = document.querySelector('.menu-toggle');
    menuToggle.addEventListener('click', togglePopup);
});

// Function to toggle the visibility of the popup menu
function togglePopup() {
    // Finds the popup menu by its ID
    var popup = document.getElementById("popupMenu");
    // Toggles the 'show' class to either display or hide the menu
    popup.classList.toggle("show");
}

// Executes when the document is fully ready
$(document).ready(function() {
    // Initializes the dropdown menus with Semantic UI's dropdown component
    $('.ui.dropdown').dropdown();
    // Initializes the rating component with Semantic UI settings (obtained from one of the tutorials)
    $('.ui.rating').rating({
        interactive: true, 
        maxRating: 5,      
        onRate: function(value) { // Callback triggered when a rating is selected
            // Updates the hidden input field with the selected rating value
            $('#starsInput').val(value);
            // Logs the selected rating to the console
            console.log("Rating set to: " + value);
        }
    });
});

// Registers a service worker if the browser supports it
if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js", { scope: '/' })
        .then(() => console.log("Service Worker Registered")) // Logs success message on successful registration
        .catch((error) => console.error("Service Worker Registration Failed:", error)); // Logs error message if registration fails
    }