document.querySelectorAll(".featurecard").forEach(card => {
    card.addEventListener("click", function (e) {
        e.stopPropagation();
        this.classList.toggle("flip");
    });
});

document.addEventListener("click", () => {
    document.querySelectorAll(".featurecard.flip").forEach(card => {
        card.classList.remove("flip");
    });
});
