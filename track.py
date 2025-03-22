import pandas as pd

def targets():

    data = {
        "category": [
            "Pessoal", "Alimentação/ Bebidas", "Saúde", "Casa", "Outros", 
            "Carro", "Pet", "Farmácia", "Total"
        ],
        "target": [
            4200, 3500, 1600, 2100, 1000, 900, 250, 150, 13700
        ]
    }

    return pd.DataFrame(data)