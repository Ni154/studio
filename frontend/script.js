const API_URL = "https://seu-backend-aqui.up.railway.app"; // substitua pela URL do seu backend no Railway

document.getElementById("formDespesa").addEventListener("submit", async function (e) {
    e.preventDefault();

    const valor = parseFloat(document.getElementById("valor").value);
    const categoria = document.getElementById("categoria").value.trim();
    const descricao = document.getElementById("descricao").value.trim();

    const response = await fetch(`${API_URL}/despesas/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            valor,
            categoria,
            descricao,
        }),
    });

    if (response.ok) {
        document.getElementById("formDespesa").reset();
        carregarDespesas();
    } else {
        alert("Erro ao adicionar despesa.");
    }
});

async function carregarDespesas() {
    const response = await fetch(`${API_URL}/despesas/`);
    const despesas = await response.json();

    const tbody = document.querySelector("#tabelaDespesas tbody");
    tbody.innerHTML = "";

    despesas.forEach((despesa) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${despesa.id}</td>
            <td>R$ ${despesa.valor.toFixed(2)}</td>
            <td>${despesa.categoria}</td>
            <td>${despesa.descricao || ""}</td>
            <td>${new Date(despesa.data).toLocaleDateString("pt-BR")}</td>
        `;
        tbody.appendChild(tr);
    });
}

document.addEventListener("DOMContentLoaded", carregarDespesas);
