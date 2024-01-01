import streamlit as st
import pandas as pd
import numpy as np
import base64
import plotly.express as px
import plotly.graph_objects as go

# Password for accessing the download
password = "95_NWDems!"
race_mapping = {1: "Other", 2: "Other", 6: "Other", 7: "Other", 9: "Other", 3: "African American", 4: "Hispanic", 5: "White"}


def create_download_link(df, filename):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'

def summarize_voting_data(df, selected_elections, selected_voter_status, selected_commission_districts, selected_party):
    df['Race'] = df['Race'].map(race_mapping).fillna(df['Race'])  # Apply mapping and fill with the original value if not found

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
    #df_voting_history = df[selected_columns].applymap(lambda x: 1 if x in ['Y', 'Z', 'A', 'E', 'F'] else 0)
    df_voting_history = df[selected_columns].apply(lambda x: x.map({'Y': 1, 'Z': 1, 'A': 1, 'E': 1, 'F': 1}).fillna(0)).astype(int)
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

def calculate_voter_counts(df, selected_race=None, selected_sex=None, selected_party=None, selected_age_range=None, selected_commission_districts=None):
    # Replace the values in the "Race" column
    df['Race'] = df['Race'].map(race_mapping).fillna(df['Race'])  # Apply mapping and fill with the original value if not found
    city_ward_mapping = {51: "District 1", 52: "District 2", 53: "District 3", 54: "District 4", 55: "District 5", 56: "District 6"}
    df['City_Ward'] = df['City_Ward'].map(city_ward_mapping).fillna('Unincorporated')
    df['Birth_Date'] = pd.to_datetime(df['Birth_Date'])
    df['Age'] = (pd.to_datetime('today').year - df['Birth_Date'].dt.year)
    age_ranges = {'18-28': (18, 28), '26-34': (26, 34), '35-55': (35, 55), '55+': (55, float('inf'))}
    df['Age Range'] = pd.cut(df['Age'], bins=[age_ranges[range_name][0]-1 for range_name in age_ranges.keys()] + [age_ranges['55+'][1]], labels=age_ranges.keys())

    # Apply filters based on selected parameters
    if selected_race:
        df = df[df['Race'].isin(selected_race)]
    
    if selected_sex:
        df = df[df['Sex'].isin(selected_sex)]
    
    if selected_party:
        df = df[df['Party'].isin(selected_party)]

    if selected_age_range:
        age_ranges = {'18-28': (18, 28), '26-34': (26, 34), '35-55': (35, 55), '55+': (55, float('inf'))}
        age_range_values = [age_ranges[range_name] for range_name in selected_age_range]
        age_filter = df['Age'].apply(lambda x: any(start <= x <= end for start, end in age_range_values))
        df = df[age_filter]
    
    if selected_commission_districts:
        df = df[df['City_Ward'].isin(selected_commission_districts)]

    # Calculate counts by Race, Sex, Party, and Age Range
    counts_by_race = df.groupby('Race').size()
    counts_by_sex = df.groupby('Sex').size()
    counts_by_party = df.groupby('Party').size()
    
    if selected_age_range:
        counts_by_age_range = df.groupby('Age Range').size()
    else:
        counts_by_age_range = None

    return counts_by_race, counts_by_sex, counts_by_party, counts_by_age_range, df


def load_data():
    df = pd.read_csv('https://serendipitytech.s3.amazonaws.com/deltona/deltona_voters_streamlit.txt', delimiter=',', low_memory=False)
    return df

st.set_page_config(layout="wide")

def page_1():
    df = load_data()

    
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

    # Create the 'Voting History' column based on selected elections
    #selected_columns = ["03-07-2023 Flagler Beach(Mar/07/2023)", "03/07/2023 Flagler Beach(Mar/07/2023)", "11-08-2022 General Election(Nov/08/2022)", "08-23-2022 Primary Election(Aug/23/2022)", "2022 City of Flagler Beach Election(Mar/08/2022)", "11-02-2021 Municipal Election(Nov/02/2021)", "Daytona Beach Special Primary(Sep/21/2021)", "Municipal Election(Aug/17/2021)", "04-13-2021 Port Orange Primary(Apr/13/2021)", "City of Flagler Beach(Mar/02/2021)", "20201103 General Election(Nov/03/2020)", "20200818 Primary Election(Aug/18/2020)", "20200519 Pierson Mail Ballot Elec(May/19/2020)", "20200317 Pres Preference Primary(Mar/17/2020)", "City of Flagler Beach(Mar/17/2020)", "20191105 Lake Helen General(Nov/05/2019)", "20190611 Pt Orange Special Runoff(Jun/11/2019)", "20190521 Mail Ballot Election(May/21/2019)", "20190430 Pt Orange Special Primary(Apr/30/2019)", "20190402 Edgewater Special General(Apr/02/2019)"]
    #df_voting_history = df[selected_elections].applymap(lambda x: 1 if x in ['Y', 'Z', 'A', 'E', 'F'] else 0)
    df_voting_history = df[selected_elections].apply(lambda x: x.map({'Y': 1, 'Z': 1, 'A': 1, 'E': 1, 'F': 1}).fillna(0)).astype(int)

    voting_history = df_voting_history[selected_elections].sum(axis=1)
    df['Voting History'] = voting_history

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

    # Adding a breakdown of age ranges in the voting history table
    st.subheader("Voting History by Age Ranges")
    summary_voting_history_by_age = df.groupby(['Age Range', 'Voting History']).size().unstack(fill_value=0)
    st.table(summary_voting_history_by_age)


def page_2():
    df = load_data()
    race_values = ["African American", "Hispanic", "White", "Other"]

    # Allow users to select Deltona Commission Districts
    city_ward_mapping = {51: "District 1", 52: "District 2", 53: "District 3", 54: "District 4", 55: "District 5", 56: "District 6"}
    city_ward_options = list(city_ward_mapping.values())
    selected_commission_districts = st.sidebar.multiselect("Select Deltona Commission Districts:", city_ward_options, key="commission_districts")
    selected_party = st.sidebar.multiselect("Select Party:", df['Party'].unique())
    selected_age_range = st.sidebar.multiselect("Select Age Range:", ["18-28", "26-34", "35-55", "55+"])

    # Create a UI for selecting filters
    selected_race = st.sidebar.multiselect("Select Race:", race_values)
    selected_sex = st.sidebar.multiselect("Select Sex:", df['Sex'].unique())
    


    # Call the calculate_voter_counts function with the selected filters
    race_counts, sex_counts, party_counts, age_range_counts, df = calculate_voter_counts(df, selected_race, selected_sex, selected_party, selected_age_range, selected_commission_districts)

    # Calculate the total number of voters based on the selected filters
    total_voters = len(df[df['Race'].isin(selected_race) &
                        df['Sex'].isin(selected_sex) &
                        df['Party'].isin(selected_party) &
                        df['Age Range'].isin(selected_age_range) &
                        df['City_Ward'].isin(selected_commission_districts)])

    
    show_percent = st.checkbox("Show Percent", value=True)

    # Create three columns to display the pie charts side by side
    col1, col2, col3 = st.columns(3)

    # Function to create a pie chart from a pandas Series
    def create_pie_chart(data, title, width=300, height=300):
        fig = go.Figure(data=[go.Pie(labels=data.index, values=data.values, textinfo="percent+label+value", showlegend=False)])
        fig.update_layout(title_text=f"{title} (Total: {data.sum()})", width=width, height=height)
        return fig

    with col1:
        st.plotly_chart(create_pie_chart(race_counts, "Voter Counts by Race", width=300, height=300))

    with col2:
        st.plotly_chart(create_pie_chart(sex_counts, "Voter Counts by Sex", width=300, height=300))

    with col3:
        st.plotly_chart(create_pie_chart(party_counts, "Voter Counts by Party", width=300, height=300))
    
    # ...

# Always display the "Voter Counts by Age Range" chart with all age ranges
    all_age_ranges = ["18-28", "26-34", "35-55", "55+"]
    age_range_counts = df.groupby('Age Range').size().reindex(all_age_ranges, fill_value=0)
    st.plotly_chart(create_pie_chart(age_range_counts, "Voter Counts by Age Range"))



    
if __name__ == '__main__':
    # Create a dropdown menu for selecting pages
    selected_page = st.sidebar.selectbox("Select a page:", ["Overview", "Additional Summaries"])

    if selected_page == "Overview":
        page_1()  # Call the Page 1 function
    elif selected_page == "Additional Summaries":
        page_2()  # Call the Page 2 function
