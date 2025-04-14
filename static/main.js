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

async function make_form_async(form) {
    form.addEventListener("submit", async (event) => {
        event.preventDefault(); // Prevent default form submission

        const formData = new FormData(form); // Gather form data
        const action = form.getAttribute('action'); // Form's action URL
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value; // CSRF Token

        const statusMessage = document.createElement("p"); // Status message element

        const previousMessage = form.querySelector(".status-message");
        if (previousMessage) {
            previousMessage.remove();
        }
        statusMessage.className = "status-message";
        form.appendChild(statusMessage);

        try {
            const response = await fetch(action, {
                method: "POST",
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken, // Include CSRF token
                },
            });

            if (!response.ok) {
                throw new Error(`Upload failed! HTTP Status: ${response.status}`);
            }

            // Parse and display success message
            const result = await response.json(); // Expecting JSON response
            statusMessage.textContent = result.message || "Upload succeeded!";
            statusMessage.style.color = "green";

            console.log("Success:", result);
        } catch (error) {
            // Handle and display error message
            statusMessage.textContent = `Upload failed! ${error.message}`;
            statusMessage.style.color = "red";

            console.error("Error occurred:", error);
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('.assignmentForm');
    if (form) {
        make_form_async(form);
    }
});

function compute_final_grade(table) {
    let totalWeight = 0;
    let weightedSum = 0;
    let finalGradeCell = table.querySelector("tfoot .numcol");

    if (!table.dataset.originalFinalGrade) {
        table.dataset.originalFinalGrade = finalGradeCell.textContent;
    }

    table.querySelectorAll("td.numcol").forEach(td => {
        const weight = parseFloat(td.dataset.weight) || 0;
        let score = 0;

        if (table.classList.contains("hypothesized")) {
            const input = td.querySelector("input");
            score = input && input.value !== "" ? parseFloat(input.value) : parseFloat(td.dataset.value) || 0;
        } else {
            score = td.textContent.includes("Missing") || td.textContent.includes("Ungraded") || td.textContent.includes("Not Due") 
                ? 0 
                : parseFloat(td.textContent.replace('%', '')) || 0;
        }

        console.log(`Weight: ${weight}, Score: ${score}`);

        if (!isNaN(score)) {
            weightedSum += (score * weight) / 100;
            totalWeight += weight;
        }
    });

    console.log(`Total Weight: ${totalWeight}, Weighted Sum: ${weightedSum}`);

    const finalGrade = totalWeight > 0 ? ((weightedSum / totalWeight) * 100).toFixed(2) : "N/A";

    if (!table.classList.contains("hypothesized")) {
        finalGradeCell.textContent = table.dataset.originalFinalGrade;
    } else {
        finalGradeCell.textContent = `${finalGrade}%`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const table = document.querySelector(".sortable");
    if (table) {
        make_grade_hypothesized(table);
    }
});

function make_grade_hypothesized(table) {
    const hypothesizeButton = document.querySelector(".hypothesizeButton");

    hypothesizeButton.addEventListener("click", () => {
        const isHypothesized = table.classList.toggle("hypothesized");

        hypothesizeButton.textContent = isHypothesized ? "Actual grades" : "Hypothesize";

        table.querySelectorAll("td.numcol").forEach(td => {
            const statusText = td.textContent.trim();

            if (statusText === "Not Due" || statusText === "Ungraded" || td.querySelector("input")) {
                if (isHypothesized) {
                    if (!td.dataset.originalText) {
                        td.dataset.originalText = statusText;
                    }
                    td.innerHTML = `<input type="number" min="0" max="100" placeholder="Enter %" class="hypothesis-input">`;
                } else {
                    td.textContent = td.dataset.originalText || td.textContent;
                    td.dataset.originalText = "";
                }
            }
        });

        compute_final_grade(table);
    });

    table.addEventListener("keyup", event => {
        if (event.target.classList.contains("hypothesis-input")) {
            compute_final_grade(table);
        }
    });
}