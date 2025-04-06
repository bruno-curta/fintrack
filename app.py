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
from ai_client import ChatCompletion


client = MongoDBConnect()
ai_client = ChatCompletion()

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
    #ui.layout_columns(
    #        ui.markdown('''<div style="color:green; text-align: left"><b>FINTRACK APP</b></div>'''),
    #    max_height='30px',
    #    col_widths=[1,11]
    #),
    ui.navset_card_tab(
        ui.nav_panel(ui.markdown('''
                            <div style="color:green; text-align: center"><b>SUBMIT</b></div>
                            '''),   
                ui.input_select('who', 'Quem pagou?', ['', 'Teste', 'Bruno', 'Ellen'], width='100%'),
                ui.input_select('forwhom', 'Para quem foi?', ['', 'Todos', 'Bruno', 'Ellen', 'Manu'], width='100%'),
                ui.input_select('how', 'Como pagou?', ['', 'Crédito', 'Pix', 'Ifood', 'Débito conta', 'Dinheiro'], width='100%'),
                ui.input_select('category', 'Categoria', list(categories.keys()), width='100%'),
                ui.input_select('subcategory', 'Subcategoria', [], width='100%'),
                ui.input_text('where', 'Onde foi?', placeholder='Local da compra', width='100%'),
                ui.input_numeric('value', 'Valor Gasto', value='', width='100%'),
                ui.input_action_button('submit', 'Enviar', width='100%', icon='🚀'),
        ),
        ui.nav_panel(ui.markdown('''
                            <div style="color:green; text-align: center"><b>TRACK</b></div>
                            '''),
            ui.page_sidebar(
                ui.sidebar('Selecione o ano e mês para visualizar os dados',
                ui.input_select('year', 'Ano', ['2025', '2026']),
                ui.input_select('month', 'Mês', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], selected=pd.to_datetime('now').month),
                ui.input_action_button('update_data', 'Mostrar Dados', width='100%', icon='💰'), 
                ),
                ui.card(
                ui.output_ui('df_update'),
                max_height='100%',
                ),
                fillable_mobile=True
                ),
        ),
        ui.nav_panel(ui.markdown('''<div style="color:green; text-align: center"><b>TABLE</b></div>'''),
            ui.input_action_button('update_table', 'Atualizar', width='100%', icon='⚡'), 
            ui.output_data_frame('df_all'),
        ),
        ui.nav_panel(ui.markdown('''<div style="color:green; text-align: center"><b>AI</b></div>'''),
            ui.card(ui.card_header("Converse com seus gastos"),
                ui.chat_ui("chat", placeholder='Digite aqui sua pergunta', width='100%',fillable_mobile=True)
            )
        )

    ),
    #fillable_mobile=True
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
        if who == '' or forwhom == '' or how == '' or category == '' or subcategory == '' or where == '' or value == None:
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
                
        start = pd.to_datetime('now')+pd.tseries.offsets.MonthEnd(-1)-pd.DateOffset(months=3)
        end = pd.to_datetime('now')+pd.tseries.offsets.MonthEnd(-1)

        def max_day(year, month):
            if month in [1, 3, 5, 7, 8, 10, 12]:
                return 'percent_acumulado_31'
            elif month in [4, 6, 9, 11]:
                return 'percent_acumulado_30'
            else:
                if year % 4 == 0 and year % 100 != 0 or year % 400 == 0:
                    return 'percent_acumulado_29'
                else:
                    return 'percent_acumulado_28'
                
        # curvas de gasto acumulado por categoria
        df_day = df.query("@start <= track_timestamp <= @end").groupby(['category','day'])['value'].sum().reset_index()
        df_day['num_months'] = df.query("@start <= track_timestamp <= @end")['month'].nunique()
        df_day['value'] = df_day['value']/df_day['num_months']
        c, d = pd.core.reshape.util.cartesian_product([pd.unique(df_day['category']), list(range(1,32))])
        df_all_day = pd.DataFrame(dict(category=c, day=d))
        df_day = pd.merge(df_all_day, df_day, on=['category','day'], how='left')
        df_day['value'] = df_day['value'].fillna(0)
        df_day['cum_value']=df_day.groupby('category')['value'].cumsum()

        df_day['percent_acumulado_28']=df_day.query('day<=28')['cum_value']/df_day.query('day<=28').groupby('category')['cum_value'].transform('max')
        df_day['percent_acumulado_29']=df_day.query('day<=29')['cum_value']/df_day.query('day<=29').groupby('category')['cum_value'].transform('max')
        df_day['percent_acumulado_30']=df_day.query('day<=30')['cum_value']/df_day.query('day<=30').groupby('category')['cum_value'].transform('max')
        df_day['percent_acumulado_31']=df_day.query('day<=31')['cum_value']/df_day.query('day<=31').groupby('category')['cum_value'].transform('max')

        df_day['expected'] = round(df_day[max_day(ano, mes)]*100)
                
        # curvas de gasto acumulado total
        df_esperado_total = df.query("@start <= track_timestamp <= @end").groupby(['day'])['value'].sum().reset_index()
        df_esperado_total['num_months'] = df.query("@start <= track_timestamp <= @end")['month'].nunique()
        df_esperado_total['value'] = df_esperado_total['value']/df_esperado_total['num_months']
        df_all_day = pd.DataFrame({'day':list(range(1,32))})
        df_esperado_total = pd.merge(df_all_day, df_esperado_total, on=['day'], how='left')
        df_esperado_total['value'] = df_esperado_total['value'].fillna(0)
        df_esperado_total['cum_value']=df_esperado_total['value'].cumsum()

        df_esperado_total['percent_acumulado_28']=df_esperado_total.query('day<=28')['cum_value']/df_esperado_total.query('day<=28')['cum_value'].max()
        df_esperado_total['percent_acumulado_29']=df_esperado_total.query('day<=29')['cum_value']/df_esperado_total.query('day<=29')['cum_value'].max()
        df_esperado_total['percent_acumulado_30']=df_esperado_total.query('day<=30')['cum_value']/df_esperado_total.query('day<=30')['cum_value'].max()
        df_esperado_total['percent_acumulado_31']=df_esperado_total.query('day<=31')['cum_value']/df_esperado_total.query('day<=31')['cum_value'].max()

        df_esperado_total['category'] = 'Total'
        df_esperado_total['value'] = df_esperado_total['cum_value']
        df_esperado_total['target'] = 13700
        df_esperado_total['expected'] = round(df_esperado_total[max_day(ano, mes)]*100)
        
        #filter df_day with the last actual day of the month from the df_final table
        last_day = df.query('year==@ano & month==@mes')['day'].max()

        df_esperado_total = df_esperado_total.query('day==@last_day')
        df_day = df_day.query('day==@last_day')
        df_esperado_total = pd.concat([df_esperado_total[['category', 'expected']], df_day[['category', 'expected']]], ignore_index=True)
        
        df_final = pd.merge(df_final, df_esperado_total, on='category', how='right')


        def highlight_SLA(row):
            green = 'background-color: green'
            yellow = 'background-color: yellow'
            pink = 'background-color: red'

            styles = [''] * len(row)  # Default empty styles for all columns

            if row['track'] <= row['expected'] * 0.95:
                styles[row.index.get_loc('track')] = green
                styles[row.index.get_loc('expected')] = green
            elif row['track'] <= row['expected']:
                styles[row.index.get_loc('track')] = yellow
                styles[row.index.get_loc('expected')] = yellow
            else:
                styles[row.index.get_loc('track')] = pink
                styles[row.index.get_loc('expected')] = pink

            return styles
        
        return ui.HTML(
                    df_final.style.hide()
                    .apply(highlight_SLA, axis=1)  # Apply row-wise
                    .format('{:.0f}', na_rep='MISS', subset=['value', 'target', 'track', 'expected'])
                    .to_html(index=False)
                )
    
    @render.data_frame
    @reactive.event(input.update_table)
    def df_all():
        df=pd.DataFrame(client.get_data())
        return render.DataGrid(df, filters=True, width='100%', height='100%')


     # Define the chat
    chat = ui.Chat(id="chat")

    @chat.on_user_submit
    async def _():
        df=pd.DataFrame(client.get_data())
        fintrack_md = df.to_markdown(index=False)
        question = chat.user_input()
        prompt = f"Here is a financial table:\n{fintrack_md}\n\nBased on this, {question}"
        answer = ai_client.chat(prompt)
        await chat.append_message(answer)

app = App(app_ui, server)

if __name__ == "__main__":
    app.run()