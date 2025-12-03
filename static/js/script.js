const menuToggle = document.getElementById("menuToggle");
const sidebar = document.getElementById("sidebar");
const closeSidebar = document.getElementById("closeSidebar");

menuToggle.addEventListener("click", () => {
    sidebar.classList.add("active");
});

closeSidebar.addEventListener("click", () => {
    sidebar.classList.remove("active");
});
