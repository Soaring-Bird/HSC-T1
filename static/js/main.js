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
