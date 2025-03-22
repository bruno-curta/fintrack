# Shiny app to collect user input on personal expenses and storage the data in a database 
# and display the data in a table and chart

from shiny import App, Inputs, Outputs, Session, ui, render, reactive

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import pandas as pd
import matplotlib.pyplot as plt
import os

from mongodb_connect import MongoDBConnect

client = MongoDBConnect()

categories = {
    '': [],
    'Alimentação/ Bebidas': ['Alimentação', 'Bebidas', 'Festas', 'Praia', 'Refeição', 'Saídas'],
    'Carro': ['Combustível', 'Estacionamento'],
    'Casa': ['Água', 'Assinaturas', 'Internet', 'Jardinagem', 'Khronos', 'Limpeza', 'Luz', 'Manutenção Casa'],
    'Farmácia': ['Higiene & Beleza'],
    'Lazer': ['Passeios'],
    'Pessoal': ['Cabelo', 'Celular', 'CNH', 'Conserto bike', 'Escola', 'Hobbies', 'Impressão', 'Livro', 'Presentes', 'Prudential', 'Roupas/ Calçado/ Etc'],
    'Pet': ['Ração/Medicamento'],
    'Saúde': ['Consulta', 'Dentista', 'Funcional/Treino', 'Terapia', 'Yoga'],
    'Outros': ['Outros']
}

app_ui = ui.page_fillable(
    ui.input_dark_mode(mode='dark'),
    ui.navset_card_tab(
        ui.nav_panel(ui.markdown('''
                            <div style="color:green; text-align: center"><b>FINTRACK &#129297;</b></div>
                            '''),
                          
                ui.input_select('who', 'Quem pagou?', ['', 'Teste', 'Bruno', 'Ellen'], width='100%'),
                ui.input_select('forwhom', 'Para quem foi?', ['', 'Todos', 'Bruno', 'Ellen', 'Manu'], width='100%'),
                ui.input_select('how', 'Como pagou?', ['', 'Crédito', 'Pix', 'Ifood', 'Débito conta', 'Dinheiro'], width='100%'),
                ui.input_select('category', 'Categoria', list(categories.keys()), width='100%'),
                ui.input_select('subcategory', 'Subcategoria', [], width='100%'),
                ui.input_text('where', 'Onde foi?', placeholder='Local da compra', width='100%'),
                ui.input_numeric('value', 'Valor Gasto', value='0.00', width='100%'),
                ui.input_action_button('submit', 'Enviar', width='100%'),
            
        ),
        ui.nav_panel(ui.markdown('''
                            <div style="color:green; text-align: center"><b>GRÁFICOS &#128200;</b></div>
                            '''),
            ui.card(ui.input_action_button('update_chart', 'Atualizar Dados', width='100%'), max_height='80px'),
            ui.output_plot('p')

        ),
        ui.nav_panel(ui.markdown('''
                            <div style="color:green; text-align: center"><b>DADOS &#128187;</b></div>
                            '''),
            ui.card(ui.input_action_button('update_data', 'Atualizar Dados', width='100%'), max_height='80px'),
            ui.output_data_frame('df_update')
        )
    ),
    
)

def server(input: Inputs, output: Outputs, session: Session):

    @reactive.Effect
    @reactive.event(input.category)
    def update_subcategories():
        selected_category = input.category()
        subcategories = categories.get(selected_category, [])
        if subcategories != []:
            subcategories.insert(len(subcategories), 'Outros')
        ui.update_select('subcategory', choices=subcategories)

    @reactive.Effect
    @reactive.event(input.submit)
    def submit_to_mongo():
        who = input.who()
        forwhom = input.forwhom()
        how = input.how()
        category = input.category()
        subcategory = input.subcategory()
        where = input.where()
        value = input.value()

        # condition to check if any input is empty and return a message for a modal warning
        if who == '' or forwhom == '' or how == '' or category == '' or subcategory == '' or where == '' or value == 0.00:
            m = ui.modal('', 'Preencha todos os campos para enviar!')
            ui.modal_show(m)
        else:
            
            track = {
                'track_timestamp': pd.to_datetime('now'),
                'who': who,
                'forwhom': forwhom,
                'how': how,
                'category': category,
                'subcategory': subcategory,
                'where': where,
                'value': value
            }

            client.insert_data(track)

            ui.update_text('where', value='')
            ui.update_numeric('value', value='0.00')
            ui.update_select('who', selected='')
            ui.update_select('forwhom', selected='')
            ui.update_select('how', selected='')
            ui.update_select('category', selected='')
            ui.update_select('subcategory', selected='')

            m = ui.modal('', 'Dados enviados com sucesso!')
            ui.modal_show(m)

    @output
    @render.data_frame
    @reactive.event(input.update_data)
    
    def df_update():
        df=pd.DataFrame(client.get_data())
        return render.DataGrid(df, filters=True, width='100%')

    @output
    @render.plot
    @reactive.event(input.update_chart)
    def p():
        df=pd.DataFrame(client.get_data())
        if df.empty:
            return None
        else:
            fig, ax = plt.subplots(figsize=(10, 6))
            y = df.loc[df.track_timestamp>=pd.to_datetime('now')-pd.tseries.offsets.DateOffset(months=2)].groupby(df.track_timestamp.dt.date)['value'].sum()
            ax.bar(y.index, y, color='purple')
            ax.set_title('Gasto Diário - últimos 2 meses')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            return plt.gcf()
    

app = App(app_ui, server)

if __name__ == "__main__":
    app.run()