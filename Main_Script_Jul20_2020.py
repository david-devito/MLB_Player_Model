#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 18 11:18:43 2020

@author: daviddevito
"""

import pandas as pd
import numpy as np
import mlbFunctions
import sys

# Expand limits of printing
pd.set_option('display.max_columns', None); pd.set_option('display.max_rows', None); pd.set_option('display.width', 1000)

# LOAD PITCHING AND HITTINGDATA
[pitching_2019_L, pitching_2019_R] = mlbFunctions.load_pitching_data()
[batting_2019_L, batting_2019_R] = mlbFunctions.load_hitting_data()

# LOAD TODAY'S LINEUPS FROM ROTOGRINDERS
[name_data, pitcher_name_data, team_name_data] = mlbFunctions.get_todays_lineups()

# CREATE LIST OF TEAMS
[team_array, team_array_pitch, home_team_array, home_team_array_pitch]= mlbFunctions.team_lists(team_name_data)
# CREATE LIST OF BATTING ORDER POSITIONS
lineupPos = []
for teami in range(0,int(len(team_array)/9)): lineupPos.extend(list(range(1,10)))

# START HITTER DATAFRAME WITH STANDARD HITTER INFO
player_df = pd.DataFrame()
player_df = mlbFunctions.hitterStandardInfo(player_df,name_data)

# CREATE DATAFRAME FOR STARTING PITCHERS
pitcher_df = pd.DataFrame()
pitcher_df = mlbFunctions.pitcherStandardInfo(pitcher_df,pitcher_name_data)


# REPLACE NAMES THAT DON'T MATCH ACROSS ALL SOURCES
replacePitchers = {}
replaceHitters = {"Matthew Beaty": "Matt Beaty","Michael Taylor": "Michael A. Taylor"}
if len(replacePitchers) > 0: pitcher_df = mlbFunctions.replacePlayerNames(replacePitchers,pitcher_df)
if len(replaceHitters) > 0: player_df = mlbFunctions.replacePlayerNames(replaceHitters,player_df)


# ADD TEAM NAME AND LINEUP ORDER TO HITTER DATAFRAME
player_df['Team'] = team_array
player_df['Order'] = lineupPos

# ADD PITCHER OPPOSITION TO PITCHER DATAFRAME
pitchOppIX = 0
pitchOppName = []
for pitcheri in range(0, int(len(team_array_pitch)/2)):
    pitchOppName.append(team_array_pitch[pitchOppIX+1])
    pitchOppName.append(team_array_pitch[pitchOppIX])
    pitchOppIX += 2
# ADD TEAM NAME TO PITCHER DATAFRAME
pitcher_df['Team'] = team_array_pitch
pitcher_df['OppTeam'] = pitchOppName

# SET INDEX OF HITTER DATAFRAME TO BE PLAYER NAME
player_df = player_df.set_index('Name')

# GET LIST OF PLAYER NAMES
playerList = player_df.index.tolist()
pitcherList = pitcher_df.index.tolist()

# CORRECT SWITCH HITTERS HANDEDNESS TO BE OPPOSITE OF PITCHERS
for playeri in playerList:
    if player_df['Hand'][playeri] == 'S':
        if player_df['PitchHand'][playeri] == 'L': player_df.at[playeri,'Hand'] = 'R'
        elif player_df['PitchHand'][playeri] == 'R': player_df.at[playeri,'Hand'] = 'L'

# COUNT NUMBER OF HITTERS OF EACH HANDEDNESS THAT PITCHER IS FACING
for playeri in pitcherList:
    pitcher_df.at[playeri,'LHB'] = player_df[(player_df['Team']==pitcher_df['OppTeam'][playeri]) & (player_df['Hand']=='L')].shape[0]
    pitcher_df.at[playeri,'RHB'] = player_df[(player_df['Team']==pitcher_df['OppTeam'][playeri]) & (player_df['Hand']=='R')].shape[0]

# POPULATE HITTER DATAFRAME WITH PLAYER STATS BASED ON OPPOSING PITCHER HANDEDNESS
statsList = ['PA','wOBA','Hard%','BB%','K%','ISO','GB%','wRC+','SB']
player_df = mlbFunctions.populateHitterStats(statsList,playerList,player_df,batting_2019_L,batting_2019_R)

# POPULATE PITCHER DATAFRAME WITH PLAYER STATS BASED ON OPPOSING HITTER HANDEDNESS
statsList = ['IP','wOBA','Hard%','BB%','K%','SLG','GB%','xFIP']
pitcher_df = mlbFunctions.populatePitcherStats(statsList,pitcherList,pitcher_df,pitching_2019_L,pitching_2019_R)

pitchRearrangeColumns = ['PitchHand','Team','OppTeam','LHB','IP_L','wOBA_L','Hard%_L','BB%_L','K%_L','SLG_L','GB%_L','xFIP_L','RHB','IP_R','wOBA_R','Hard%_R','BB%_R','K%_R','SLG_R','GB%_R','xFIP_R']
pitcher_df = pitcher_df[pitchRearrangeColumns]
pitcher_df['Home Team'] = home_team_array_pitch


# LOAD PARK FACTORS BY HANDEDNESS
park_LHB = pd.read_csv('stats_csvFiles/FantasyPros_ParkFactors_L.csv'); park_LHB = park_LHB.set_index('Team')
park_RHB = pd.read_csv('stats_csvFiles/FantasyPros_ParkFactors_R.csv'); park_RHB = park_RHB.set_index('Team')

for playeri in playerList:
    if player_df['Hand'][playeri] == 'L': player_df.at[playeri,'ParkRuns'] = park_LHB['CombinedHits'][home_team_array[player_df.index.tolist().index(playeri)]]
    elif player_df['Hand'][playeri] == 'R': player_df.at[playeri,'ParkRuns'] = park_RHB['CombinedHits'][home_team_array[player_df.index.tolist().index(playeri)]]

# SUBTRACT MEAN OF EACH STATISTIC FROM EACH COLUMN IN HITTER DATAFRAME
statsList = player_df.columns[6:-2].tolist()
for stati in statsList:
    #Account for Park Factors
    if stati == 'wOBA' or stati == 'ISO':
        tempStat = player_df[stati].values
        player_df[stati] = np.multiply(tempStat,player_df['ParkRuns'].values)
    #statMean = np.nanmean(player_df[stati].values)
    #player_df[stati] = player_df[stati].values - statMean

# CALCULATE PROJECTED POINTS FOR EACH HITTER
betaVals = [4.37975860e+00, -1.14905084e-01, -6.06442617e-01, -6.19732814e-02, 2.07716098e+00, 1.00958264e-01, -3.97282014e-04, 1.00539250e-02]
regIntercept = 0.06383379772034004
player_df['ProjPerPA'] = (player_df['wOBA']*betaVals[0]) + (player_df['Hard%']*betaVals[1]) + (player_df['BB%']*betaVals[2]) + (player_df['K%']*betaVals[3]) + \
                (player_df['ISO']*betaVals[4]) + (player_df['GB%']*betaVals[5]) + (player_df['wRC+']*betaVals[6]) + (player_df['SB']*betaVals[7]) + regIntercept
lineupSpotBoost = [1.11,1.08,1.08,1.04,0.99,0.96,0.93,0.89,0.84]      
PAsPerLineupSpot = [4.65,4.55,4.43,4.33,4.24,4.13,4.01,3.9,3.77]
ChangeByLineupSpot = np.multiply(lineupSpotBoost,PAsPerLineupSpot)
player_df['ProjPts'] = np.multiply(player_df['ProjPerPA'].values,ChangeByLineupSpot[player_df['Order'].values-1])

# SUBTRACT MEAN OF EACH STATISTIC FROM EACH COLUMN IN PITCHER DATAFRAME
statsList = pitcher_df.columns[3:-1].tolist()
for stati in statsList:
    #Account for Park Factors
    if stati == 'wOBA_L' or stati == 'SLG_L' or stati == 'xFIP_L':
        tempStat = pitcher_df[stati].values
        pitcher_df[stati] = np.multiply(tempStat,park_LHB['CombinedHits'][pitcher_df['Home Team'].values].values)
    if stati == 'wOBA_R' or stati == 'SLG_R' or stati == 'xFIP_R':
        tempStat = pitcher_df[stati].values
        pitcher_df[stati] = np.multiply(tempStat,park_RHB['CombinedHits'][pitcher_df['Home Team'].values].values)
    # Subtract mean from values
    #if stati != 'IP_L' and stati != 'IP_R' and stati != 'LHB' and stati != 'RHB':
    #    statMean = np.nanmean(pitcher_df[stati].values)
    #    pitcher_df[stati] = pitcher_df[stati].values - statMean


# INSERT BLANK COLUMN BETWEEN LHB AND RHB PITCHING STATS
blankCol = ""
pitcher_df.insert(12, '-', blankCol)

bullpenDF = mlbFunctions.getBullpenStats()
# Add Batters faced by Handedness to Bullpen DF
bullpenDF = pd.concat([bullpenDF,pitcher_df[['Team','LHB','RHB']].set_index('Team')],axis=1); bullpenDF = bullpenDF[['LHB','vsL','RHB','vsR']]
# Sort bullpenDF by order of pitcher_df
bullpenDF = bullpenDF.reindex(pitcher_df['Team'].values.tolist())

# Reorder Pitcher Dataframe
pitcher_df['Name'] = pitcher_df.index.values.tolist(); pitcher_df = pitcher_df.set_index('Team')
orderTemp = pitcher_df.columns.tolist()[:-1]; orderTemp.insert(0,'Name'); pitcher_df = pitcher_df[orderTemp]
# Combine Pitcher and Bullpen Dataframe
pitcher_df = pd.concat([pitcher_df[pitcher_df.columns[:-1]],bullpenDF],axis=1)
pitcher_df.insert(22, 'Bullpen', blankCol)

# REPLACE PLAYER NAMES WITH THOSE USED BY DRAFTKINGS
replacePitchers = {}
replaceHitters = {"Enrique Hernandez": "Kike Hernandez"}
if len(replacePitchers) > 0: pitcher_df = mlbFunctions.replacePlayerNames(replacePitchers,pitcher_df)
player_df['Name'] = player_df.index.values
if len(replaceHitters) > 0: player_df = mlbFunctions.replacePlayerNames(replaceHitters,player_df)
# ADD SALARIES TO HITTER DATAFRAME
DKSalaries = pd.read_csv('stats_csvFiles/DKSalaries.csv'); DKSalaries = DKSalaries.set_index('Name')
player_df = player_df.set_index('Name')
player_df['Salary'] = DKSalaries['Salary'][player_df.index.values].values
pitcher_salary = DKSalaries['Salary'][pitcher_df['Name']].values
pitcher_df.insert(2, 'Salary', pitcher_salary)

# SAVE DATAFRAMES TO CSV FILES
player_df.to_csv('Output/player_df.csv')
pitcher_df.to_csv('Output/pitcher_df.csv')


