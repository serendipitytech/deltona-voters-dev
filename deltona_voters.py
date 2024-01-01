import streamlit as st
import pandas as pd
import numpy as np
import base64

# Password for accessing the download
password = "95_NWDems!"

def create_download_link(df, filename):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'

def summarize_voting_data(df, selected_elections, selected_voter_status, selected_commission_districts, selected_party):
    race_mapping = {1: "Other", 2: "Other", 6: "Other", 9: "Other", 3: "African American", 4: "Hispanic", 5: "White"}
    df['Race'] = df['Race'].map(race_mapping)

    city_ward_mapping = {51: "District 1", 52: "District 2", 53: "District 3", 54: "District 4", 55: "District 5", 56: "District 6"}
    df['City_Ward'] = df['City_Ward'].map(city_ward_mapping).fillna('Unincorporated')

    sex_mapping = {"M": "M", "F": "F", "U": "U"}
    df['Sex'] = df['Sex'].map(sex_mapping)

    df['Birth_Date'] = pd.to_datetime(df['Birth_Date'])
    df['Age'] = (pd.to_datetime('today').year - df['Birth_Date'].dt.year)

    age_ranges = {'18-28': (18, 28), '26-34': (26, 34), '35-55': (35, 55), '55+': (55, float('inf'))}
    df['Age Range'] = pd.cut(df['Age'], bins=[age_ranges[range_name][0]-1 for range_name in age_ranges.keys()] + [age_ranges['55+'][1]], labels=age_ranges.keys())
    
    if selected_voter_status:
        df = df[df['Status'].isin(selected_voter_status)]

    if selected_commission_districts:
        df = df[df['City_Ward'].isin(selected_commission_districts)]

    if selected_party:
        df = df[df['Party'].isin(selected_party)]
    
    summary_age = df.groupby(['Race', 'Sex', 'Age Range']).size().unstack(fill_value=0)
    race_order = ["African American", "Hispanic", "White", "Other"]
    sex_order = ["M", "F", "U"]
    summary_age = summary_age.reindex(race_order, level='Race')
    summary_age = summary_age.reindex(sex_order, level='Sex')
    summary_age = summary_age.reindex(sex_order, level='Sex')
    summary_age.index = summary_age.index.map(lambda x: f'{x[0]}, {sex_mapping[x[1]]}')  # Combine the multi-index levels into a single string

    row_totals_age = summary_age.sum(axis=1)
    column_totals_age = summary_age.sum(axis=0)

    selected_columns = ["03-07-2023 Flagler Beach(Mar/07/2023)", "03/07/2023 Flagler Beach(Mar/07/2023)", "11-08-2022 General Election(Nov/08/2022)", "08-23-2022 Primary Election(Aug/23/2022)", "2022 City of Flagler Beach Election(Mar/08/2022)", "11-02-2021 Municipal Election(Nov/02/2021)", "Daytona Beach Special Primary(Sep/21/2021)", "Municipal Election(Aug/17/2021)", "04-13-2021 Port Orange Primary(Apr/13/2021)", "City of Flagler Beach(Mar/02/2021)", "20201103 General Election(Nov/03/2020)", "20200818 Primary Election(Aug/18/2020)", "20200519 Pierson Mail Ballot Elec(May/19/2020)", "20200317 Pres Preference Primary(Mar/17/2020)", "City of Flagler Beach(Mar/17/2020)", "20191105 Lake Helen General(Nov/05/2019)", "20190611 Pt Orange Special Runoff(Jun/11/2019)", "20190521 Mail Ballot Election(May/21/2019)", "20190430 Pt Orange Special Primary(Apr/30/2019)", "20190402 Edgewater Special General(Apr/02/2019)"]
    df_voting_history = df[selected_columns].applymap(lambda x: 1 if x in ['Y', 'Z', 'A', 'E', 'F'] else 0)
    voting_history = df_voting_history[selected_elections].sum(axis=1)
    df['Voting History'] = voting_history

    summary_voting_history = df.groupby(['Race', 'Sex', 'Voting History']).size().unstack(fill_value=0)
    summary_voting_history = summary_voting_history.reindex(race_order, level='Race')
    summary_voting_history = summary_voting_history.reindex(sex_order, level='Sex')
    summary_voting_history.index = summary_voting_history.index.map(lambda x: f'{x[0]}, {sex_mapping[x[1]]}')  # Combine the multi-index levels into a single string

    num_elections = len(selected_elections)

    summary_voting_history.columns = [f'{i} of {num_elections}' for i in range(num_elections + 1)]

    # Calculate summary for all parties
    summary_party_history = df.groupby(['Race', 'Sex', 'Voting History', 'Party']).size().unstack(fill_value=0)

    # Create a custom index combining race, sex, and number of elections
    summary_party_history.index = summary_party_history.index.map(lambda x, num_elections=num_elections: f'{x[0]} {x[1]}, {x[2]} of last {num_elections} elections')

    summary_voting_history.columns = [f'{i} of {num_elections}' for i in range(num_elections + 1)]

    row_totals_voting_history = summary_voting_history.sum(axis=1)
    column_totals_voting_history = summary_voting_history.sum(axis=0)

    columns_for_detailed_age = ["VoterID", "Race", "Sex", "Birth_Date", "Precinct"]
    columns_for_detailed_voting_history = ["VoterID", "Race", "Sex", "Birth_Date", "Precinct"] + selected_elections

    return summary_age, row_totals_age, column_totals_age, df[columns_for_detailed_age], summary_voting_history, row_totals_voting_history, column_totals_voting_history, df[columns_for_detailed_voting_history], summary_party_history

def load_data():
    df = pd.read_csv('https://serendipitytech.s3.amazonaws.com/deltona/deltona_voters_streamlit.txt', delimiter=',', low_memory=False)
    return df

def main():
    df = load_data()

    st.set_page_config(layout="wide")
    st.title("Welcome to the Deltona Voting Data Summary App")
    st.write("""
        The intent of this app is to quick some quick counts on voters in your precinct.
        - **Step 1:** Open the side bar if you do not see it now. There will be a small arrow icon in the top left corner that you click or tap to open the side bar.
        - **Step 2:** Select the elections you wish to consider from the dropdown menu on the left.
        - **Step 3:** Select the precincts and districts from the dropdown menu on the left to add additional filters.
        - **Note:** You can select multiple precincts, districts, and elections, and the counts will update with those selections.
        """)
    st.sidebar.title("Filter Selections:")
    
    voter_status = df['Status'].unique().tolist()
    selected_voter_status = st.sidebar.multiselect("Select Voter Status:", voter_status, default=['ACT'], key="voter_status")

    city_ward_mapping = {51: "District 1", 52: "District 2", 53: "District 3", 54: "District 4", 55: "District 5", 56: "District 6"}
    city_ward_options = list(city_ward_mapping.values())
    selected_commission_districts = st.sidebar.multiselect("Select Deltona Commission Districts:", city_ward_options, key="commission_districts")

    party_options = df['Party'].unique().tolist()
    selected_party = st.sidebar.multiselect("Selected Party:", party_options, key="party")
    
    selected_elections = st.sidebar.multiselect("Select up to three elections:", ["11-08-2022 General Election(Nov/08/2022)", "08-23-2022 Primary Election(Aug/23/2022)", "20201103 General Election(Nov/03/2020)", "20200818 Primary Election(Aug/18/2020)", "20200317 Pres Preference Primary(Mar/17/2020)", "11-02-2021 Municipal Election(Nov/02/2021)", "Municipal Election(Aug/17/2021)", "20190521 Mail Ballot Election(May/21/2019)", "20190402 Edgewater Special General(Apr/02/2019)", "20191105 Lake Helen General(Nov/05/2019)", "Daytona Beach Special Primary(Sep/21/2021)", "20190430 Pt Orange Special Primary(Apr/30/2019)", "04-13-2021 Port Orange Primary(Apr/13/2021)", "20190611 Pt Orange Special Runoff(Jun/11/2019)", "20200519 Pierson Mail Ballot Elec(May/19/2020)", "City of Flagler Beach(Mar/02/2021)", "City of Flagler Beach(Mar/17/2020)", "03-07-2023 Flagler Beach(Mar/07/2023)", "03/07/2023 Flagler Beach(Mar/07/2023)", "2022 City of Flagler Beach Election(Mar/08/2022)"], default=["11-08-2022 General Election(Nov/08/2022)", "08-23-2022 Primary Election(Aug/23/2022)", "20201103 General Election(Nov/03/2020)"], key="elections")

   # get the summaries and detailed records
    summary_age, row_totals_age, column_totals_age, detailed_age, summary_voting_history, row_totals_voting_history, column_totals_voting_history, detailed_voting_history, summary_party_history = summarize_voting_data(df, selected_elections, selected_voter_status, selected_commission_districts, selected_party)
    summary_age.index = summary_age.index.to_series().replace({'M': 'Male', 'F': 'Female', 'U': 'Unreported'}, regex=True)
    summary_voting_history.index = summary_voting_history.index.to_series().replace({'M': 'Male', 'F': 'Female', 'U': 'Unreported'}, regex=True)

    st.subheader("Voting Data Summary by Age Ranges")
    summary_age.loc['Column Total'] = summary_age.sum()
    summary_age['Row Total'] = summary_age.sum(axis=1)
    st.table(summary_age)

    st.subheader("Voting History by Race and Sex")
    summary_voting_history.loc['Column Total'] = summary_voting_history.sum()
    st.table(summary_voting_history)

    st.subheader("Voting History by Race, Sex, and Party")
    summary_party_history.loc['Column Total'] = summary_party_history.sum()
    st.table(summary_party_history)
    
if __name__ == '__main__':
    main()
