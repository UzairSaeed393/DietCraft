
document.addEventListener("DOMContentLoaded", function () {

    /* =========================
       FOOD PREFERENCES – ALL
    ========================== */
    const foodContainer = document.getElementById("food-chips");
    if (foodContainer) {
        const foodCheckboxes = foodContainer.querySelectorAll("input[type='checkbox']");
        const allCheckbox = Array.from(foodCheckboxes).find(cb => cb.value === "all");

        if (allCheckbox) {
            allCheckbox.addEventListener("change", () => {
                foodCheckboxes.forEach(cb => {
                    if (cb !== allCheckbox) {
                        cb.checked = allCheckbox.checked;
                    }
                });
            });

            foodCheckboxes.forEach(cb => {
                if (cb !== allCheckbox) {
                    cb.addEventListener("change", () => {
                        if (!cb.checked) {
                            allCheckbox.checked = false;
                        }
                    });
                }
            });
        }
    }

    /* =========================
       MEDICAL CONDITIONS – NONE
    ========================== */
    const medicalContainer = document.getElementById("medical-chips");
    if (medicalContainer) {
        const medicalCheckboxes = medicalContainer.querySelectorAll("input[type='checkbox']");
        const noneCheckbox = Array.from(medicalCheckboxes).find(cb => cb.value === "none");

        if (noneCheckbox) {
            noneCheckbox.addEventListener("change", () => {
                if (noneCheckbox.checked) {
                    medicalCheckboxes.forEach(cb => {
                        if (cb !== noneCheckbox) {
                            cb.checked = false;
                            cb.disabled = true;
                        }
                    });
                } else {
                    medicalCheckboxes.forEach(cb => {
                        cb.disabled = false;
                    });
                }
            });

            medicalCheckboxes.forEach(cb => {
                if (cb !== noneCheckbox) {
                    cb.addEventListener("change", () => {
                        if (cb.checked) {
                            noneCheckbox.checked = false;
                            medicalCheckboxes.forEach(x => x.disabled = false);
                        }
                    });
                }
            });
        }
    }

});

