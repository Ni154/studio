from datetime import datetime

def formatar_data_br(data_str: str) -> str:
    """Formata string AAAA-MM-DD para DD/MM/AAAA"""
    try:
        dt = datetime.strptime(data_str, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except:
        return data_str

def formatar_moeda(valor: float) -> str:
    """Formata valor float para moeda brasileira (R$ 0,00)"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

