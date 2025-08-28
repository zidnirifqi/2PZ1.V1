document.addEventListener("DOMContentLoaded", function() {
    const menuItems = document.querySelectorAll(".menu-it li");

    menuItems.forEach(item => {
        item.addEventListener("click", () => {
            alert("Anda memilih: " + item.textContent);
        });
    });
});


