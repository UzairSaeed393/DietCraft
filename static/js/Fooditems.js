document.addEventListener('DOMContentLoaded', function () {
    const search = document.getElementById('foodSearch');
    const typeFilter = document.getElementById('typeFilter');
    const mealFilter = document.getElementById('mealFilter');
    const clearBtn = document.getElementById('clearFilters');
    const table = document.getElementById('foodTable');
    const rows = Array.from(table.querySelectorAll('tbody .food-row'));
    const prevBtn = document.getElementById("prevPage");
    const nextBtn = document.getElementById("nextPage");
    const pageInfo = document.getElementById("pageInfo");
    let currentPage = 1;

    function getText(row) {
        return (
            row.querySelector('.name').innerText + ' ' +
            row.querySelector('.type').innerText + ' ' +
            row.querySelector('.suitability').innerText + ' ' +
            row.querySelector('.cal').innerText + ' ' +
            row.querySelector('.carb').innerText + ' ' +
            row.querySelector('.fat').innerText + ' ' +
            row.querySelector('.protein').innerText
        ).toLowerCase();
    }

    function matchesFilters(row) {
        const q = search.value.trim().toLowerCase();
        const t = typeFilter.value.trim().toLowerCase();
        const m = mealFilter.value.trim().toLowerCase();

        const text = getText(row);
        const rowType = row.querySelector('.type').innerText.toLowerCase();
        const rowMeal = row.querySelector('.suitability').innerText.toLowerCase();

        const matchesQuery = q === '' || text.includes(q);
        const matchesType = t === '' || rowType.includes(t);
        const matchesMeal = m === '' || rowMeal.includes(m);

        return matchesQuery && matchesType && matchesMeal;
    }

    function getRowsPerPage() {
        return window.innerWidth <= 992 ? 20 : 50;
    }

    function renderTable() {
        const filteredRows = rows.filter(matchesFilters);
        const rowsPerPage = getRowsPerPage();
        const totalPages = filteredRows.length ? Math.ceil(filteredRows.length / rowsPerPage) : 0;

        rows.forEach(row => {
            row.style.display = 'none';
        });

        if (!filteredRows.length) {
            pageInfo.textContent = 'No matching food items';
            prevBtn.disabled = true;
            nextBtn.disabled = true;
            return;
        }

        currentPage = Math.min(currentPage, totalPages);
        const start = (currentPage - 1) * rowsPerPage;
        const end = start + rowsPerPage;

        filteredRows.slice(start, end).forEach(row => {
            row.style.display = '';
        });

        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        prevBtn.disabled = currentPage === 1;
        nextBtn.disabled = currentPage === totalPages;
    }

    function refreshFromFilters() {
        currentPage = 1;
        renderTable();
    }

    let typing;
    search.addEventListener('input', () => {
        clearTimeout(typing);
        typing = setTimeout(refreshFromFilters, 120);
    });

    typeFilter.addEventListener('change', refreshFromFilters);
    mealFilter.addEventListener('change', refreshFromFilters);
    clearBtn.addEventListener('click', function (e) {
        e.preventDefault();
        search.value = '';
        typeFilter.value = '';
        mealFilter.value = '';
        refreshFromFilters();
    });
    // Enhance responsive rows with labels for mobile
    function ensureDataLabels() {
        const headers = Array.from(table.querySelectorAll('thead th')).map(h => h.innerText.trim());
        table.querySelectorAll('tbody tr').forEach(tr => {
            tr.querySelectorAll('td').forEach((td, i) => {
                td.setAttribute('data-label', headers[i] || '');
            });
        });
    }

    ensureDataLabels();

    prevBtn.onclick = () => {
        if (currentPage > 1) {
            currentPage--;
            renderTable();
            window.scrollTo({top:0,behavior:"smooth"});
        }
    };

    nextBtn.onclick = () => {
        const filteredRows = rows.filter(matchesFilters);
        const totalPages = filteredRows.length ? Math.ceil(filteredRows.length / getRowsPerPage()) : 0;
        if (currentPage < totalPages) {
            currentPage++;
            renderTable();
            window.scrollTo({top:0,behavior:"smooth"});
        }
    };

    /* Recalculate on resize */
    window.addEventListener("resize", () => {
        currentPage = 1;
        renderTable();
    });

    renderTable();
});
