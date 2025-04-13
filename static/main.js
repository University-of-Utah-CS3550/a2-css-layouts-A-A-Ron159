function say_hi(elt) {
    console.log("Welcome to", elt.innerText);
}

say_hi(document.querySelector("h1"));

function make_table_sortable(table) {
    const headers = table.querySelectorAll('thead th.sort-column');
    const tbody = table.querySelector('tbody');
    const originalOrder = Array.from(tbody.querySelectorAll('tr'));

    headers.forEach(header => {
        header.addEventListener('click', () => {
            const columnIndex = header.cellIndex;
            let rows = Array.from(tbody.querySelectorAll('tr'));

            headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));

            let sortState = header.dataset.sortState || 'unsorted';
            if (sortState === 'unsorted') {
                sortState = 'sort-asc';
                header.className = 'sort-asc';
            } else if (sortState === 'sort-asc') {
                sortState = 'sort-desc';
                header.className = 'sort-desc';
            } else {
                sortState = 'unsorted';
                header.className = '';
            }
            header.dataset.sortState = sortState;

            if (sortState === 'unsorted') {
                rows = [...originalOrder];
            } else {
                rows.sort((rowA, rowB) => {
                    const cellA = rowA.querySelector(`td:nth-child(${columnIndex + 1})`);
                    const cellB = rowB.querySelector(`td:nth-child(${columnIndex + 1})`);

                    const valueA = parseFloat(cellA?.getAttribute('data-value')) || 0;
                    const valueB = parseFloat(cellB?.getAttribute('data-value')) || 0;

                    return sortState === 'sort-asc' ? valueA - valueB : valueB - valueA;
                });
            }

            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const table = document.querySelector('.sortable');
    if (table) {
        make_table_sortable(table);
    }
});