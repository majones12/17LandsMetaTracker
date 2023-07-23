'''
Using 17-lands color_ratings data to track changes in the meta

Mike Jones  July 9th, 2023
'''
from datetime import datetime, timedelta
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
import pandas as pd
from matplotlib import pyplot as plt
import inquirer
import os


def get_table_values(table_html: BeautifulSoup) -> dict:
    '''
    returns a dictionary where key = deck name, and value is tuple
    (wins, games, rate)
    '''
    record = {}
    rows_list = table_html.find_all('tr', class_='color-individual')
    if not rows_list:  # no rows found
        return {}
    for row in rows_list:
        cells = row.find_all('td')
        record[cells[0].string] = (int(cells[1].string),
                                   int(cells[2].string))
    rows_list = table_html.find_all('tr', class_='color-summary')
    for row in rows_list:
        cells = row.find_all('td')
        if cells[0].string in ['Four-color', 'Four-color + Splash',
                               'Five-color']:
            record[cells[0].string] = (int(cells[1].string),
                                       int(cells[2].string))
    return record


def scrape(selected_expansion: str, selected_format: str,
           selected_group: str, new_from: any = False) -> pd.DataFrame:
    # driver and already loaded items from page are still in scope
    expansion.select_by_value(selected_expansion)
    time.sleep(0.5)
    formats.select_by_value(selected_format)
    time.sleep(0.5)
    group = '' if selected_group == 'All Users' else selected_group
    users.select_by_value(group)
    # get new to and from dates
    try:
        from_xpath = '//*[@id="app"]/div/div[1]/div[4]/div/div[1]/div/input'
        from_date_in = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, from_xpath)))
        to_xpath = '//*[@id="app"]/div/div[1]/div[4]/div/div[3]/div/input'
        to_date_in = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, to_xpath)))
    except Exception as e:
        print(e)

    if new_from:
        from_date_in.click()
        time.sleep(0.5)
        from_date_in.send_keys(Keys.CONTROL, 'a')
        time.sleep(0.5)
        from_date_in.send_keys(datetime.strftime(new_from, '%m/%d/%Y'))
        time.sleep(5)
    
    from_date = datetime.strptime(from_date_in.get_attribute('value'),
                                  '%m/%d/%Y')
    to_date = datetime.strptime(to_date_in.get_attribute('value'),
                                '%m/%d/%Y')
    print(f"From: {from_date:%m-%d-%Y} To: {to_date:%m-%d-%Y}")
    # to date seems to always be today regardless of expansion
    # so when scraping, when get an empty table - stop processing
    # (mark as done or ...)
    try:
        table = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, 'table'))
        )
    except Exception as e:
        print(e)
    print(f"Scraping: {selected_expansion} {selected_format} {selected_group}")
    table_html = BeautifulSoup(table.get_attribute('innerHTML'), 'html.parser')
    last_table = get_table_values(table_html)
    all_decks = last_table.keys()
    
    data = []
    cur_date = from_date + timedelta(days=1)
    data_exists = True
    while (cur_date <= to_date) and data_exists:
        print(f" Processing: {cur_date:%m-%d-%Y}")
        # set the from date
        from_date_in.click()
        time.sleep(0.5)
        from_date_in.send_keys(Keys.CONTROL, 'a')
        time.sleep(0.5)
        from_date_in.send_keys(datetime.strftime(cur_date, '%m/%d/%Y'))
        time.sleep(15)
        # wait for table to reload
        try:
            table = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, 'table'))
            )
        except Exception as e:
            print(e)

        table_html = BeautifulSoup(table.get_attribute('innerHTML'),
                                   'html.parser')
        cur_table = get_table_values(table_html)
        if not cur_table:  # current table is empty
            print(f" No more data as of {cur_date:%d-%m-%Y}")
            data_exists = False
        for deck in all_decks:
            if deck in last_table and deck in cur_table:
                wins = last_table[deck][0] - cur_table[deck][0]
                games = last_table[deck][1] - cur_table[deck][1]
            elif deck in last_table:
                wins = last_table[deck][0]
                games = last_table[deck][1]
            elif deck in cur_table:
                print('I didnt expect this to happen - note the date.')
                wins = cur_table[deck][0]
                games = cur_table[deck][1]
            else:
                wins = 0
                games = 0
            record = {'date': cur_date - timedelta(days=1),
                      'format': selected_expansion,
                      'deck': deck,
                      'wins': wins,
                      'games': games}
            data.append(record)
        cur_date = cur_date + timedelta(days=1)
        if cur_date > to_date and data_exists:  # add most recent data
            wins = last_table[deck][0]
            games = last_table[deck][1]
            record = {'date': cur_date - timedelta(days=1),
                      'format': selected_expansion,
                      'deck': deck,
                      'wins': wins,
                      'games': games}
            data.append(record)
        last_table = cur_table

    data_df = pd.DataFrame(data)
    return data_df


if __name__ == '__main__':
    url = "https://www.17lands.com/color_ratings"

    # to suppress Certificate parsing error
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(options=options)
    
    driver.get(url)

    try:
        expansion_in = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, 'expansion')))
        format_in = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, 'format')))
        users_in = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.NAME, 'user-group')))
        from_xpath = '//*[@id="app"]/div/div[1]/div[4]/div/div[1]/div/input'
        from_date_in = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, from_xpath)))
        to_xpath = '//*[@id="app"]/div/div[1]/div[4]/div/div[3]/div/input'
        to_date_in = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, to_xpath)))
    except Exception as e:
        print(e)

    expansion = Select(expansion_in)
    cur_expansion = expansion.first_selected_option.get_attribute('value')

    formats = Select(format_in)
    cur_format = formats.first_selected_option.get_attribute('value')

    users = Select(users_in)
    cur_users = users.first_selected_option.get_attribute('value')
    cur_users = 'All Users' if not cur_users else cur_users
    # user_groups = [x.text for x in users.options] # shows text option
    # All Users = ''
    user_groups = [x.get_attribute('value') for x in users.options]  

    from_date = datetime.strptime(from_date_in.get_attribute('value'),
                                  '%m/%d/%Y')
    to_date = datetime.strptime(to_date_in.get_attribute('value'), '%m/%d/%Y')

    print('Current Selections:')
    print(f"Expansion: {cur_expansion}")
    print(f"Format: {cur_format}")
    print(f"User Group: {cur_users}")
    print(f"From: {from_date:%m-%d-%Y} To: {to_date:%m-%d-%Y}")
    print()

    questions = [
        inquirer.List(
            'expansion',
            message='Choose Expansion',
            choices=[x.get_attribute('value') for x in expansion.options]
        )
    ]
    answers = inquirer.prompt(questions)
    selected_expansion = answers['expansion']
    
    questions = [
        inquirer.List(
            'format',
            message='Choose Format',
            choices=[x.get_attribute('value') for x in formats.options]
        )
    ]
    answers = inquirer.prompt(questions)
    selected_format = answers['format']

    questions = [
        inquirer.List(
            'group',
            message='Choose User Group',
            choices=[x.text for x in users.options]
        )
    ]
    answers = inquirer.prompt(questions)
    selected_group = answers['group']

    # Now check to see if we have a file for the users choice
    # if we do, open it and load data else - scrape the data and create file
    # if the loaded data is current set, and max date in loaded data is < today
    #  then update the current set data by scraping only the new data
    filename = f"./cache/{selected_expansion}_{selected_format}_{selected_group}.csv"
    if os.path.exists(filename):
        data = pd.read_csv(filename, index_col=0, parse_dates=['date'])
        max_date = data['date'].max()
        print(max_date.date(), (datetime.today()-timedelta(days=1)).date())
        if (max_date.date() < (datetime.today()-timedelta(days=1)).date()) and \
           (selected_expansion == cur_expansion):
            print('Updating the data with latest.')
            updated_data = scrape(selected_expansion, selected_format,
                                  selected_group,
                                  new_from=max_date + timedelta(days=1))
            data = pd.concat([data, updated_data], ignore_index=True)
            data.to_csv(filename)
    else:
        # scrape for the data and create the file
        data = scrape(selected_expansion, selected_format, selected_group)
        data.to_csv(filename)
    
    driver.quit()
    ########################################################
    #  Create the graph                                    #
    ########################################################
    # might make the following a config file - allow user to select grouping
    deck_map = {'Mono-White': 'Mono', 'Mono-Blue': 'Mono',
                'Mono-Black': 'Mono', 'Mono-Red': 'Mono', 'Mono-Green': 'Mono',
                'Mono-White + Splash': 'Mono',
                'Mono-Blue + Splash': 'Mono', 'Mono-Black + Splash': 'Mono',
                'Mono-Red + Splash': 'Mono', 'Mono-Green + Splash': 'Mono',
                'Azorius (WU)': 'WU', 'Dimir (UB)': 'UB', 'Rakdos (BR)': 'BR',
                'Gruul (RG)': 'RG', 'Selesnya (GW)': 'GW', 'Orzhov (WB)': 'WB',
                'Golgari (BG)': 'BG', 'Simic (GU)': 'GU', 'Izzet (UR)': 'UR',
                'Boros (RW)': 'RW', 'Azorius (WU) + Splash': 'WU',
                'Dimir (UB) + Splash': 'UB', 'Rakdos (BR) + Splash': 'BR',
                'Gruul (RG) + Splash': 'RG', 'Selesnya (GW) + Splash': 'GW',
                'Orzhov (WB) + Splash': 'WB', 'Golgari (BG) + Splash': 'BG',
                'Simic (GU) + Splash': 'GU', 'Izzet (UR) + Splash': 'UR',
                'Boros (RW) + Splash': 'RW', 'Jeskai (WUR)': 'Other',
                'Sultai (UBG)': 'Other',
                'Mardu (BRW)': 'Other', 'Temur (RGU)': 'Other',
                'Abzan (GWB)': 'Other',
                'Esper (WUB)': 'Other', 'Grixis (UBR)': 'Other',
                'Jund (BRG)': 'Other',
                'Naya (RGW)': 'Other', 'Bant (GWU)': 'Other',
                'Jeskai (WUR) + Splash': 'Other',
                'Sultai (UBG) + Splash': 'Other',
                'Mardu (BRW) + Splash': 'Other',
                'Temur (RGU) + Splash': 'Other',
                'Abzan (GWB) + Splash': 'Other',
                'Esper (WUB) + Splash': 'Other',
                'Grixis (UBR) + Splash': 'Other',
                'Jund (BRG) + Splash': 'Other', 'Naya (RGW) + Splash': 'Other',
                'Bant (GWU) + Splash': 'Other', 'Four-color': 'Other',
                'Four-color + Splash': 'Other', 'Five-color': 'Other'}
    
    data['two_color_group'] = data['deck'].map(deck_map)
    games_per_day = (data[['date', 'games']].groupby('date').sum()).squeeze()
    grouped_data = data.groupby(['date', 'two_color_group']).sum()
    grouped_data = grouped_data.reset_index(level=0)
    grouped_data['games_per_day'] = grouped_data['date'].map(games_per_day)
    grouped_data['percentage'] = grouped_data['games'] / grouped_data['games_per_day']
    grouped_data['percentage'] = grouped_data['percentage'] * 100
    deck_list = ['Mono', 'BR', 'BG', 'WB', 'UB', 'WU', 'RW', 'GW',
                 'UR', 'GU', 'RG', 'Other']
    merged = pd.DataFrame()
    for deck in deck_list:
        temp_df = grouped_data[grouped_data.index == deck][['date', 'percentage']]
        temp_df.rename(columns={'percentage': deck}, inplace=True)
        temp_df = temp_df.set_index('date')
        merged = merged.merge(temp_df, left_index=True,
                              right_index=True, how='outer')
    
    # re-order the columns based on means of each
    merged = merged.reindex(merged.mean().sort_values(ascending=False).index,
                            axis=1)
    # re-sort colors based on new order
    decks = ['Mono', 'BG', 'BR', 'WB', 'UB', 'WU', 'RW',
             'GW', 'UR', 'GU', 'RG', 'Other']
    colors = ['#000000', '#204523', '#472728', '#818282', '#326080',
              '#99bee8', '#f0787a', '#7cf078', '#6102a1', '#02a199',
              '#73541c', '#ff9900']
    color_lookup = dict(zip(decks, colors))
    plot_colors = [color_lookup[x] for x in merged.columns]
    line_styles = ['-', '--', '-.', ':', '-', '--', '-.', ':', '-',
                   '--', '-.', ':']
    plt.rcParams['figure.figsize'] = [11, 8]
    plt.rcParams['figure.autolayout'] = True
    plt.rcParams['figure.titlesize'] = 'x-large'
    ax1 = merged.plot(title=f'{selected_expansion} {selected_format} {selected_group}', 
                      zorder=2, ylabel='% of games played', color=plot_colors, 
                      style=line_styles)
    ax1.set_zorder(2)
    ax1.set_facecolor('none')
    #ax1.tick_params(axis='x', labelrotation=90)
    ax2 = ax1.twinx()
    ax2.bar(games_per_day.index, games_per_day.values, zorder=1, color='lightblue',
            label='Games Played', width=0.6)
    ax2.set_zorder(1)
    ax2.legend(loc='upper right')
    plt.show()

    ## Win percentage Analysis - what's winning as time progresses
    grouped_data['win percentage'] = grouped_data['wins'] / grouped_data['games']
    grouped_data['win percentage'] = grouped_data['win percentage'] * 100
    win_data = pd.DataFrame()
    for deck in deck_list:
        temp_df = grouped_data[grouped_data.index == deck][['date', 'win percentage']]
        temp_df.rename(columns={'win percentage': deck}, inplace=True)
        temp_df = temp_df.set_index('date')
        win_data = win_data.merge(temp_df, left_index=True,
                                  right_index=True, how='outer')
        
    
    #win_data[merged.columns].plot(title=f"Win % {selected_expansion} {selected_format} {selected_group}", 
    #                              color=plot_colors, style=line_styles,
    #                              ylabel='Win Percentage')
    
    win_data[merged.columns].boxplot(ylabel='Win Percentage', xlabel='Deck')
    max_date = datetime.strftime(win_data.index.max(), '%Y-%m-%d')
    plt.title(f"{selected_expansion} {selected_format} {selected_group} as of {max_date}")
    #print(win_data.describe())
    plt.show()