function say_hi(elt) {
    console.log("Welcome to", elt.innerText);
}

say_hi(document.querySelector("h1"));

function make_table_sortable(table) {
    const headerCell = table.querySelector('thead th:last-child');
    let sortState = 'unsorted';

    headerCell.addEventListener('click', () => {
        if (sortState === 'unsorted' || sortState === 'sort-desc') {
            sortState = 'sort-asc';
            headerCell.className = 'sort-asc';
        } else {
            sortState = 'sort-desc';
            headerCell.className = 'sort-desc';
        }

        if (sortState === 'sort-asc') {
            headerCell.classList.remove('sort-desc');
        } else if (sortState === 'sort-desc') {
            headerCell.classList.remove('sort-asc');
        }

        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));

        rows.sort((rowA, rowB) => {
            const cellA = rowA.querySelector('td:last-child').textContent;
            const cellB = rowB.querySelector('td:last-child').textContent;

            const valueA = parseFloat(cellA.replace('%', ''));
            const valueB = parseFloat(cellB.replace('%', ''));

            return sortState === 'sort-asc' ? valueA - valueB : valueB - valueA;
        });

        rows.forEach(row => tbody.appendChild(row));
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const table = document.querySelector('.sortable');
    if (table) {
        make_table_sortable(table);
    }
});