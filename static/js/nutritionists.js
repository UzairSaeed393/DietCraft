function toggleDetails(button) {
    const card = button.closest(".nutri-card");
    const details = card.querySelector(".nutri-expand");

    details.classList.toggle("show");

    button.innerText = details.classList.contains("show")
        ? "Hide Details"
        : "View Details";

    if (details.classList.contains("show")) {
        details.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
}
