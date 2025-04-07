import pandas as pd
from mongodb_connect import MongoDBConnect

client = MongoDBConnect()

def prepare_df(year, month):
    year = int(year)
    month = int(month)

    df=pd.DataFrame(client.get_data())
    df['year'] = df['track_timestamp'].dt.year
    df['month'] = df['track_timestamp'].dt.month
    df['day'] = df['track_timestamp'].dt.day

    df_totals = df.groupby(['year', 'month'])['value'].sum().reset_index()
    df_totals['category'] = 'Total'

    df_category = df.groupby(['year', 'month',  'category'])['value'].sum().reset_index()
    df_track = pd.concat([df_category, df_totals], ignore_index=True)

    df_track = df_track.merge(targets(), on='category', how='left').sort_values(by=['year', 'month', 'category'])
    df_track['track'] = round(df_track['value']/df_track['target']*100,1)

    return df_track.loc[(df_track.year == year) & (df_track.month == month), ['category', 'value', 'target', 'track']]

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

def max_day(year, month):
    year = int(year)
    month = int(month)
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 'percent_acumulado_31'
    elif month in [4, 6, 9, 11]:
        return 'percent_acumulado_30'
    else:
        if year % 4 == 0 and year % 100 != 0 or year % 400 == 0:
            return 'percent_acumulado_29'
        else:
            return 'percent_acumulado_28'

def prep_expected_target(df, year, month, start, end, type):

    df_esperado_category = df.query("@start <= track_timestamp <= @end").groupby(['category','day'])['value'].sum().reset_index()
    df_esperado_category['num_months'] = df.query("@start <= track_timestamp <= @end")['month'].nunique()
    df_esperado_category['value'] = df_esperado_category['value']/df_esperado_category['num_months']
    c, d = pd.core.reshape.util.cartesian_product([pd.unique(df_esperado_category['category']), list(range(1,32))])
    df_all_day_category = pd.DataFrame(dict(category=c, day=d))
    df_esperado_category = pd.merge(df_all_day_category, df_esperado_category, on=['category','day'], how='left')
    df_esperado_category['value'] = df_esperado_category['value'].fillna(0)
    df_esperado_category['cum_value']=df_esperado_category.groupby('category')['value'].cumsum()

    if type == 'expected':
        df_esperado_category['percent_acumulado_28']=df_esperado_category.query('day<=28')['cum_value']/df_esperado_category.query('day<=28').groupby('category')['cum_value'].transform('max')
        df_esperado_category['percent_acumulado_29']=df_esperado_category.query('day<=29')['cum_value']/df_esperado_category.query('day<=29').groupby('category')['cum_value'].transform('max')
        df_esperado_category['percent_acumulado_30']=df_esperado_category.query('day<=30')['cum_value']/df_esperado_category.query('day<=30').groupby('category')['cum_value'].transform('max')
        df_esperado_category['percent_acumulado_31']=df_esperado_category.query('day<=31')['cum_value']/df_esperado_category.query('day<=31').groupby('category')['cum_value'].transform('max')

        df_esperado_category['expected'] = round(df_esperado_category[max_day(year, month)]*100)
    else:
        # cruzar com o target e dividir o cum_value pelo target
        df_esperado_category = df_esperado_category.merge(targets(), on='category', how='left')
        df_esperado_category['expected'] = round(df_esperado_category['cum_value']/df_esperado_category['target']*100)
        df_esperado_category['expected'] = df_esperado_category['expected'].fillna(0)

    # curvas de gasto acumulado total
    df_esperado_total = df.query("@start <= track_timestamp <= @end").groupby(['day'])['value'].sum().reset_index()
    df_esperado_total['num_months'] = df.query("@start <= track_timestamp <= @end")['month'].nunique()
    df_esperado_total['value'] = df_esperado_total['value']/df_esperado_total['num_months']
    df_all_day_total = pd.DataFrame({'day':list(range(1,32))})
    df_esperado_total = pd.merge(df_all_day_total, df_esperado_total, on=['day'], how='left')
    df_esperado_total['value'] = df_esperado_total['value'].fillna(0)
    df_esperado_total['cum_value']=df_esperado_total['value'].cumsum()

    if type == 'expected':
        df_esperado_total['percent_acumulado_28']=df_esperado_total.query('day<=28')['cum_value']/df_esperado_total.query('day<=28')['cum_value'].max()
        df_esperado_total['percent_acumulado_29']=df_esperado_total.query('day<=29')['cum_value']/df_esperado_total.query('day<=29')['cum_value'].max()
        df_esperado_total['percent_acumulado_30']=df_esperado_total.query('day<=30')['cum_value']/df_esperado_total.query('day<=30')['cum_value'].max()
        df_esperado_total['percent_acumulado_31']=df_esperado_total.query('day<=31')['cum_value']/df_esperado_total.query('day<=31')['cum_value'].max()

        df_esperado_total['category'] = 'Total'
        df_esperado_total['value'] = df_esperado_total['cum_value']
        df_esperado_total['target'] = 13700
        df_esperado_total['expected'] = round(df_esperado_total[max_day(year, month)]*100)
    else:
        # cruzar com o target e dividir o cum_value pelo target
        df_esperado_total['category'] = 'Total'
        df_esperado_total['target'] = 13700
        df_esperado_total['expected'] = round(df_esperado_total['cum_value']/df_esperado_total['target']*100)
        df_esperado_total['expected'] = df_esperado_total['expected'].fillna(0)

    df_esperado_dia = pd.concat([df_esperado_category,df_esperado_total])
    df_esperado_dia = df_esperado_dia[['category', 'day', 'expected']]

    return df_esperado_dia

def expected_target(year, month):
    year = int(year)
    month = int(month)

    df=pd.DataFrame(client.get_data())
    df['year'] = df['track_timestamp'].dt.year
    df['month'] = df['track_timestamp'].dt.month
    df['day'] = df['track_timestamp'].dt.day

    start = pd.to_datetime('now')+pd.tseries.offsets.MonthEnd(-1)-pd.DateOffset(months=3)
    end = pd.to_datetime('now')+pd.tseries.offsets.MonthEnd(-1)

    # curvas de gasto acumulado por categoria
    df_esperado_dia = prep_expected_target(df, year, month, start, end, 'expected')
    
    start_actual = pd.Timestamp(year=year, month=month, day=1)
    end_actual = start_actual + pd.offsets.MonthEnd(0)

    df_realizado_dia = prep_expected_target(df, year, month, start_actual, end_actual, 'actual')

    df_trend = df_esperado_dia.merge(df_realizado_dia, on=['category', 'day'], how='left', suffixes=('_expected', '_realized'))
    print(df_trend)
    #filter df_day with the last actual day of the month from the df_final table
    last_day = df.query("year==@year & month==@month")['day'].max()

    df_esperado_ld = df_esperado_dia.query('day==@last_day')[['category', 'expected']]    

    return df_esperado_ld, df_trend

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