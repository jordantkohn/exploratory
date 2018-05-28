import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import ttest_ind
import re

#load in the file and delimit by newline since some university towns contain commas
uni_towns_imp = pd.read_csv('university_towns.txt', error_bad_lines=False, header=None, names = ['RegionName'],sep='\n')

#let's use quarterly GDP data in 2009 dollars, starting in the year 2000
gdp = pd.read_excel('gdplev.xls', usecols='E:G', header=5).iloc[214:]
del gdp['GDP in billions of current dollars']
gdp.columns = ['GDP 09 dlr']

#Load in the housing prices dataset
z_housing = pd.read_csv('City_Zhvi_AllHomes.csv',index_col=[2])

# Use this dictionary to map state names from two letter acronyms
states = {'OH': 'Ohio', 'KY': 'Kentucky', 'AS': 'American Samoa', 'NV': 'Nevada', 'WY': 'Wyoming',
'NA': 'National', 'AL': 'Alabama', 'MD': 'Maryland', 'AK': 'Alaska', 'UT': 'Utah', 'OR': 'Oregon',
'MT': 'Montana', 'IL': 'Illinois', 'TN': 'Tennessee', 'DC': 'District of Columbia', 'VT': 'Vermont',
'ID': 'Idaho', 'AR': 'Arkansas', 'ME': 'Maine', 'WA': 'Washington', 'HI': 'Hawaii', 'WI': 'Wisconsin',
'MI': 'Michigan', 'IN': 'Indiana', 'NJ': 'New Jersey', 'AZ': 'Arizona', 'GU': 'Guam', 'MS': 'Mississippi',
'PR': 'Puerto Rico', 'NC': 'North Carolina', 'TX': 'Texas', 'SD': 'South Dakota', 'MP': 'Northern Mariana Islands',
'IA': 'Iowa', 'MO': 'Missouri', 'CT': 'Connecticut', 'WV': 'West Virginia', 'SC': 'South Carolina', 'LA': 'Louisiana',
'KS': 'Kansas', 'NY': 'New York', 'NE': 'Nebraska', 'OK': 'Oklahoma', 'FL': 'Florida', 'CA': 'California',
'CO': 'Colorado', 'PA': 'Pennsylvania', 'DE': 'Delaware', 'NM': 'New Mexico', 'RI': 'Rhode Island', 'MN': 'Minnesota',
'VI': 'Virgin Islands', 'NH': 'New Hampshire', 'MA': 'Massachusetts', 'GA': 'Georgia', 'ND': 'North Dakota', 'VA': 'Virginia'}



#Returns a dataframe of states and university towns in the U.S.
def get_list_of_university_towns():
    #create a field for state
    uni_towns = uni_towns_imp
    uni_towns['State'] = np.NaN
    #identify the states by the presence of string "[edit]" and add them to the State field
    for i in range(0,len(uni_towns)-1):
        if re.search(r'\[edit\]',uni_towns['RegionName'][i]):
            uni_towns.loc[i,'State']=uni_towns['RegionName'][i]
    #forward fill the nulls to populate the proper state for each university town
    uni_towns['State'] = uni_towns['State'].ffill()
    #clean up the extra text, get rid of the state-state rows, set state as index
    uni_towns = uni_towns[['State', 'RegionName']].replace(r'\[edit\]', '', regex=True).replace(r' \(.*', '', regex=True)
    uni_towns = uni_towns[uni_towns.State != uni_towns.RegionName].reset_index()
    del uni_towns['index']

    return uni_towns


#Returns the year and quarter of the start of the first recession in our data
def get_recession_start():
    #find and return the first quarter of the recession. defined by two consecuive quarters of negative GDP growth
    rec_start = ''
    for i in range(2,len(gdp)):
        if ((gdp['GDP 09 dlr'][i] < gdp['GDP 09 dlr'][i-1]) and (gdp['GDP 09 dlr'][i-1] < gdp['GDP 09 dlr'][i-2])):
            rec_start = gdp.index[i-1]
            break

    return str(rec_start)

print('First quarter of recession: ' + get_recession_start())

#Returns the year and quarter of the recession end time
def get_recession_end():
    rec_start_row = gdp.index.get_loc(get_recession_start())
    #begin looking for the recession end only after one has begun
    for i in range(rec_start_row,len(gdp)):
        if ((gdp['GDP 09 dlr'][i] > gdp['GDP 09 dlr'][i-1]) and (gdp['GDP 09 dlr'][i-1] > gdp['GDP 09 dlr'][i-2])):
            rec_end = gdp.index[i]
            break

    return str(rec_end)

print('Last quarter of recession: ' + get_recession_end())

#Returns the quarter of the lowest GDP throughout the recession
def get_recession_bottom():
        rec_start_row = gdp.index.get_loc(get_recession_start())
        rec_end_row = gdp.index.get_loc(get_recession_end())
        return str(gdp.iloc[rec_start_row:rec_end_row+1]['GDP 09 dlr'].idxmin())

print('Bottom of recession: ' + get_recession_bottom())


#convert the housing data from monthly to quarterly
def convert_housing_data_to_quarters():
        #convert the states dictionary to a dataframe
        states1 = pd.DataFrame(list(states.items()), columns=['abbr', 'State'])
        #replace the state abbreviations with full state names in the housing dataframe
        housing = pd.merge(z_housing, states1, how='left', left_index=True, right_on='abbr').set_index(['State', 'RegionName'])
        del housing['abbr']
        #use only data starting with January 2000
        c = housing.columns.tolist()
        cols = c[49:]
        housing = housing[cols].sort_index()
        #use pandas PeriodIndex to convert monthly data to quarterly using the mean price
        housing = housing.groupby(pd.PeriodIndex(housing.columns, freq='q'), axis=1).mean()
        cols1 = []
        for x in housing.columns: cols1.append(str(x).lower())
        housing.columns = cols1

        return housing


print('Converted housing data from monthly to quarterly!')


#Test null hypothesis: the mean price ratio (quarter before the recession start / bottom quarter of recession)
#of university towns is not significantly different from non-university towns
def run_ttest():
    housing = convert_housing_data_to_quarters()
    #make a new dataframe for the price ratio
    a = housing.columns.get_loc(get_recession_start()) - 1
    b = housing.columns.get_loc(get_recession_bottom())
    housing['price_ratio'] = housing[housing.columns[a]]/housing[housing.columns[b]]
    housing100 = pd.DataFrame(housing['price_ratio'])

    uni_towns1 = get_list_of_university_towns()

    #get a dataframe of price ratios for university towns
    housing_uni = pd.merge(housing100, uni_towns1, left_index=True, right_on=['State','RegionName']).set_index(['State', 'RegionName'])
    #get a dataframe of price ratios for non-university towns
    index_to_keep = housing100.index.symmetric_difference(housing_uni.index)
    housing_non = housing100.loc[index_to_keep]

    #perform an independent sample t-test
    test1 = stats.ttest_ind(housing_uni['price_ratio'], housing_non['price_ratio'], equal_var=False, nan_policy='omit')

    accrej = 'fail to reject'
    lowhigh = 'less'

    if test1.pvalue < 0.01:
        accrej = 'reject'
        if housing_uni['price_ratio'].mean() > housing_non['price_ratio'].mean():
            lowhigh = 'greater'
    else: lowhigh = 'neither greater nor less'

    result = 'With a p-value of ' + str(test1.pvalue) + ', we ' + accrej + ' the null hypothesis at the significance level of 0.01.'
    result2 = 'The decline in housing prices in university towns was ' + lowhigh + ' than that of non-university towns during the recession in 2008-2009.'
    result3 = 'The mean university town ratio of pre-recession to recession-bottom housing prices is ' + str(round(housing_uni['price_ratio'].mean(),4)) + '.'
    result4 = 'That of non-university towns is ' + str(round(housing_non['price_ratio'].mean(),4)) + '.'


    return result + '\n' + result2 + '\n' + result3 + '\n' + result4


print(run_ttest())
