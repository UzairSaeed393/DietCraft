document.addEventListener('DOMContentLoaded', function () {
    const search = document.getElementById('foodSearch');
    const typeFilter = document.getElementById('typeFilter');
    const clearBtn = document.getElementById('clearFilters');
    const table = document.getElementById('foodTable');

    function getText(row) {
        return (
            row.querySelector('.name').innerText + ' ' +
            row.querySelector('.type').innerText + ' ' +
            row.querySelector('.cal').innerText + ' ' +
            row.querySelector('.carb').innerText + ' ' +
            row.querySelector('.fat').innerText + ' ' +
            row.querySelector('.protein').innerText
        ).toLowerCase();
    }

    function applyFilter() {
        const q = search.value.trim().toLowerCase();
        const t = typeFilter.value.trim().toLowerCase();
        const rows = table.querySelectorAll('tbody .food-row');

        rows.forEach(row => {
            const text = getText(row);

            const matchesQuery = q === '' || text.includes(q);
            const matchesType = t === '' || row.querySelector('.type').innerText.toLowerCase().includes(t);

            if (matchesQuery && matchesType) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    let typing;
    search.addEventListener('input', () => {
        clearTimeout(typing);
        typing = setTimeout(applyFilter, 120);
    });

    typeFilter.addEventListener('change', applyFilter);
    clearBtn.addEventListener('click', function (e) {
        e.preventDefault();
        search.value = '';
        typeFilter.value = '';
        applyFilter();
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
});

const rows = Array.from(document.querySelectorAll(".food-row"));
let currentPage = 1;

/* Responsive rows per page */
function getRowsPerPage(){
    return window.innerWidth <= 992 ? 20 : 50;
}

const prevBtn = document.getElementById("prevPage");
const nextBtn = document.getElementById("nextPage");
const pageInfo = document.getElementById("pageInfo");

function renderTable(){
    const rowsPerPage = getRowsPerPage();
    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;

    rows.forEach((row, index)=>{
        row.style.display =
            index >= start && index < end ? "" : "none";
    });

    const totalPages = Math.ceil(rows.length / rowsPerPage);
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;

    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;
}

prevBtn.onclick = () => {
    if(currentPage > 1){
        currentPage--;
        renderTable();
        window.scrollTo({top:0,behavior:"smooth"});
    }
};

nextBtn.onclick = () => {
    const totalPages =
        Math.ceil(rows.length / getRowsPerPage());
    if(currentPage < totalPages){
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
