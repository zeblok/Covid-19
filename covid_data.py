import numpy as np
import pandas as pd
from datetime import date, timedelta

def load_covid_data():
    # get county level data
    df_health_rank = pd.read_csv('data/covid_uncover/county_health_rankings/county_health_rankings/us-county-health-rankings-2020.csv')
    df_pm = pd.read_csv('data/pm_covid/PM_COVID/Data/county_pm25.csv')
    df_esri = pd.read_csv('data/covid_uncover/esri_covid-19/esri_covid-19/cdcs-social-vulnerability-index-svi-2016-overall-svi-county-level.csv')

    head_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/'

    # Check the past 5 days for the most recent data
    for i in range(5):
        day = date.today() - timedelta(days=i)
        url = head_url + day.strftime("%m-%d-%Y") + ".csv"
        try:
            df_daily_cases = pd.read_csv(url)
            break
        except:
            pass
    

    # Merge covid-19 and us county data
    
    # Only look at us cases
    df_us_daily_cases = df_daily_cases[df_daily_cases['Country_Region']=='US'].copy()

    # rename columns for convenience
    df_us_daily_cases.rename(columns={'Admin2': 'county', 'Province_State': 'state', 'FIPS': 'fips', 'Deaths': 'deaths', 'Confirmed': 'cases'}, inplace=True)

    # make all countries start with their first death
    df_us_daily_cases = df_us_daily_cases[df_us_daily_cases['deaths']!=0]
    
    # average polution particulates
    avg_pm25 = df_pm.groupby("fips").pm25.agg("mean")
    
    maxDeaths = df_us_daily_cases.groupby(['county', 'state', 'fips']).deaths.agg('max')  # get cumulative number of deaths
    pop = df_health_rank.groupby(['county', 'state', 'fips']).population_2.agg('max')  # total population
    probDeath = (np.log(maxDeaths / pop)).to_frame().reset_index().rename(columns={0:'prDeath'})
    
    df = pd.merge(probDeath, df_health_rank, how='left', left_on=['county', 'state', 'fips'], right_on = ['county', 'state', 'fips'])
    df = pd.merge(df, df_esri.drop(['state'], axis=1), how='left', left_on=['county', 'fips'], right_on=['county', 'fips'])
    df = pd.merge(df, avg_pm25, how='left', left_on=['fips'], right_on=['fips'])
    
    # population per square mile
    df['pop_density']=df['population_2'] / df['area_sqmi']
    
    # raw number indicators
    rawnum = [c for c in df.columns if 'num_' in c]
    
    # convert raw numbers to incidence levels
    df[[r+"_per_100k" for r in rawnum]] = df[rawnum].div(df['population_2'], axis=0) * 100000
    df.drop(rawnum, axis=1, inplace=True)
    
    # drop 95% confidence intervals 
    drop = [c for c in df.columns if '95' in c] + ['population']
    df.drop(drop, axis=1, inplace=True)
    
    # remove raw counts in favor of percentages
    drop = [c for c in df.columns if c[:2] == 'e_' or c[:2] == 'm_']
    df.drop(drop, axis=1, inplace=True)

    # drop ID type columns
    drop = ['county', 'state', 'st_abbr', 'st', 'objectid']
    df.drop(drop, axis=1, inplace=True)

    return df
