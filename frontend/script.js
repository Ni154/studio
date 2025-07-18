const API_URL = "http://localhost:5000"; // Ajuste para seu backend

const form = document.getElementById("formDespesa");
const tbody = document.querySelector("#tabelaDespesas tbody");

async function fetchDespesas() {
    const res = await fetch(`${API_URL}/despesas`);
    const despesas = await res.json();

    tbody.innerHTML = "";
    despesas.forEach(d => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${d.id}</td>
            <td>R$ ${d.valor.toFixed(2)}</td>
            <td>${d.categoria}</td>
            <td>${d.descricao}</td>
            <td>${new Date(d.data).toLocaleDateString('pt-BR')}</td>
        `;
        tbody.appendChild(tr);
    });
}

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const valor = parseFloat(document.getElementById("valor").value);
    const categoria = document.getElementById("categoria").value.trim();
    const descricao = document.getElementById("descricao").value.trim();

    await fetch(`${API_URL}/despesas`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ valor, categoria, descricao })
    });

    form.reset();
    fetchDespesas();
});

fetchDespesas();

