# Shiny app to collect user input on personal expenses and storage the data in a database 
# and display the data in a table and chart

from shiny import App, Inputs, Outputs, Session, ui, render, reactive

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import pandas as pd
# import matplotlib.pyplot as plt
import os

from mongodb_connect import MongoDBConnect
from track import targets


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
    ui.layout_columns(
            ui.input_dark_mode(mode='dark'),
            ui.markdown('''<div style="color:green; text-align: left"><b>FINTRACK</b></div>'''),
        max_height='30px',
        col_widths=[1,11]
    ),
    ui.navset_card_tab(
        ui.nav_panel(ui.markdown('''
                            <div style="color:green; text-align: center"><b>FIN</b></div>
                            '''),
                          
                ui.input_select('who', 'Quem pagou?', ['', 'Teste', 'Bruno', 'Ellen'], width='100%'),
                ui.input_select('forwhom', 'Para quem foi?', ['', 'Todos', 'Bruno', 'Ellen', 'Manu'], width='100%'),
                ui.input_select('how', 'Como pagou?', ['', 'Crédito', 'Pix', 'Ifood', 'Débito conta', 'Dinheiro'], width='100%'),
                ui.input_select('category', 'Categoria', list(categories.keys()), width='100%'),
                ui.input_select('subcategory', 'Subcategoria', [], width='100%'),
                ui.input_text('where', 'Onde foi?', placeholder='Local da compra', width='100%'),
                ui.input_numeric('value', 'Valor Gasto', value='', width='100%'),
                ui.markdown('''<br><br>'''),
                ui.input_action_button('submit', 'Enviar', width='100%'),
        ),
        ui.nav_panel(ui.markdown('''
                            <div style="color:green; text-align: center"><b>TRACK</b></div>
                            '''),
            ui.card(
                ui.layout_columns(
                ui.input_select('year', 'Ano', ['2025', '2026'], width='45%'),
                ui.input_select('month', 'Mês', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], selected=pd.to_datetime('now').month, width='45%')
                ),
                max_height='100px'),
            ui.card(ui.input_action_button('update_data', 'Mostrar Dados', width='100%'), max_height='80px'),
            ui.output_ui('df_update')
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
        if who == '' or forwhom == '' or how == '' or category == '' or subcategory == '' or where == '' or value == '':
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
            ui.update_numeric('value', value='')
            ui.update_select('who', selected='')
            ui.update_select('forwhom', selected='')
            ui.update_select('how', selected='')
            ui.update_select('category', selected='')
            ui.update_select('subcategory', selected='')

            m = ui.modal('', 'Dados enviados com sucesso!')
            ui.modal_show(m)

    @output
    @render.ui
    @reactive.event(input.update_data)
    
    def df_update():
        df=pd.DataFrame(client.get_data())
        df['year'] = df['track_timestamp'].dt.year
        df['month'] = df['track_timestamp'].dt.month
        df['day'] = df['track_timestamp'].dt.day
        target = targets()

        df_totals = df.groupby(['year', 'month'])['value'].sum().reset_index()
        df_totals['category'] = 'Total'

        df_category = df.groupby(['year', 'month',  'category'])['value'].sum().reset_index()
        df_track = pd.concat([df_category, df_totals], ignore_index=True)

        df_track = df_track.merge(target, on='category', how='left').sort_values(by=['year', 'month', 'category'])
        df_track['track'] = round(df_track['value']/df_track['target']*100,1)

        ano = int(input.year())
        mes = int(input.month())
        df_final = df_track.loc[(df_track['year']==ano) & (df_track['month']==mes), ['category', 'value', 'target', 'track']]
        
        def highlight_SLA(series):
            green = 'background-color: green'
            yellow = 'background-color: yellow'
            pink = 'background-color: red'
            return [green if value <= 95 else yellow if value <100 else pink for value in series]
        
        return ui.HTML(df_final.style.hide().apply(highlight_SLA, subset=['track']).format('{:.0f}', na_rep='MISS', subset=['value', 'target', 'track']).to_html(index=False))

app = App(app_ui, server)

if __name__ == "__main__":
    app.run()