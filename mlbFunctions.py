#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 20 14:56:01 2020

@author: daviddevito
"""

from pybaseball import pitching_stats, batting_stats
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests


def load_pitching_data():
    pitching_2019_L = pitching_stats(2019, end_season=None, league='all', qual=1, ind=0, handVar='L')
    pitching_2019_R = pitching_stats(2019, end_season=None, league='all', qual=1, ind=0, handVar='R')
    # Restrict data to only players with more than 9 IP
    pitching_2019_L = pitching_2019_L[pitching_2019_L['IP'] >= 9]
    pitching_2019_R = pitching_2019_R[pitching_2019_R['IP'] >= 9]
    return pitching_2019_L, pitching_2019_R

def load_hitting_data():
    batting_2019_L = batting_stats(2019, end_season=None, league='all', qual=1, ind=0, handVar='L')
    batting_2019_R = batting_stats(2019, end_season=None, league='all', qual=1, ind=0, handVar='R')
    batting_2019_L = batting_2019_L[batting_2019_L['AB'] >= 30]
    batting_2019_R = batting_2019_R[batting_2019_R['AB'] >= 30]
    return batting_2019_L, batting_2019_R

def get_todays_lineups():
    url = "https://rotogrinders.com/lineups/mlb?site=draftkings"
    r = requests.get(url)    
    soup = BeautifulSoup(r.content, "lxml")
    name_data = soup.find_all("div", {"class": "info"})
    pitcher_name_data = soup.find_all("div", {"class": "pitcher players"})
    team_name_data = soup.find_all("div", {"class": "teams"})
    return name_data, pitcher_name_data, team_name_data


def team_lists(team_name_data):
    team_array = []
    team_array_pitch = []
    home_team_array = []
    home_team_array_pitch = []
    
    for matchupi in range(0,len(team_name_data)):
        team_array = team_array + [team_name_data[matchupi].findAll('span',class_="shrt")[0].text]*9
        team_array = team_array + [team_name_data[matchupi].findAll('span',class_="shrt")[1].text]*9
        home_team_array = home_team_array + [team_name_data[matchupi].findAll('span',class_="shrt")[1].text]*18
        home_team_array_pitch = home_team_array_pitch + [team_name_data[matchupi].findAll('span',class_="shrt")[1].text]*2
        team_array_pitch.append(team_name_data[matchupi].findAll('span',class_="shrt")[0].text)
        team_array_pitch.append(team_name_data[matchupi].findAll('span',class_="shrt")[1].text)
    return team_array, team_array_pitch, home_team_array, home_team_array_pitch

def pitcherStandardInfo(fullDF,pitcher_name_data):
    for k in range(0,(len(pitcher_name_data))):
        pitcherName = pitcher_name_data[k].a.text
        pitcherHand = pitcher_name_data[0].find('span',class_='stats').text[18]
        fullDF = fullDF.append({'PitchName': pitcherName, 'PitchHand': pitcherHand}, ignore_index=True)
    fullDF = fullDF.set_index('PitchName')
    return fullDF


def hitterStandardInfo(fullDF,name_data):
    for i in range(0,len(name_data)):
        pName = name_data[i].a["title"]
        pos = name_data[i].find('span',class_='position').text
        pos = " ".join(pos.split())
        hand = name_data[i].find('span',{'class':'stats','data-hand':['L','R','S']}).text[41]
        pHand = name_data[i].find('span',{'class':'stats','data-hand':['L','R','S']})["data-opp-pitcher-hand"]
        fullDF = fullDF.append({'Name': pName, 'Pos': pos, 'Hand': hand, 'PitchHand': pHand}, ignore_index=True)

    # REARRANGE COLUMNS IN HITTER DATAFRAME
    cols = fullDF.columns.tolist()
    colsTemp = [cols[1], cols[3], cols[0], cols[2]]
    fullDF = fullDF[colsTemp]
    return fullDF

def replacePlayerNames(replaceList,fullDF):
    fullDF = fullDF.copy()
    for replaceNamei in range(0,fullDF.shape[0]):
        if fullDF['Name'][replaceNamei] in replaceList:
            fullDF['Name'][replaceNamei] = replaceList[fullDF['Name'][replaceNamei]]
    return fullDF


def populateHitterStats(statsList,playerList,fullDF,hitStatsVsL,hitStatsVsR):
    for stati in statsList:
        for playeri in playerList:
            try:
                if stati != 'PA' and fullDF.at[playeri,'PA'] == 0:
                    fullDF.at[playeri,stati]=np.NaN
                elif fullDF.at[playeri,'PitchHand'] == 'R':
                    fullDF.at[playeri,stati]=hitStatsVsR[hitStatsVsR['Name'] == playeri][stati].item()
                elif fullDF.at[playeri,'PitchHand'] == 'L':
                    fullDF.at[playeri,stati]=hitStatsVsL[hitStatsVsL['Name'] == playeri][stati].item()
            except:
                fullDF.at[playeri,stati]= 0
    return fullDF

def populatePitcherStats(statsList,pitcherList,fullDF,pitchStatsVsL,pitchStatsVsR):
    for stati in statsList:
        for playeri in pitcherList:
            try:
                if stati != 'IP' and fullDF.at[playeri,'IP_L'] == 0:
                    fullDF.at[playeri,stati + '_L']=np.NaN
                else:
                    fullDF.at[playeri,stati + '_L']=pitchStatsVsL[pitchStatsVsL['Name'] == playeri][stati].item()
            except:
                fullDF.at[playeri,stati + '_L']= 0
            try:
                if stati != 'IP' and fullDF.at[playeri,'IP_R'] == 0:
                    fullDF.at[playeri,stati + '_R']=np.NaN
                else:
                    fullDF.at[playeri,stati + '_R']=pitchStatsVsR[pitchStatsVsR['Name'] == playeri][stati].item()
            except:
                fullDF.at[playeri,stati + '_R']= 0
    return fullDF



def getBullpenStats():
    # LOAD PITCHING AND HITTINGDATA
    [pitching_2019_L, pitching_2019_R] = load_pitching_data()
    
    
    
    teamAbbrev = pd.read_csv('stats_csvFiles/teamAbbrev.csv'); teamAbbrev = teamAbbrev.set_index('Abbrev')
    
    DKSalaries = pd.read_csv('stats_csvFiles/DKSalaries.csv'); DKSalaries = DKSalaries.set_index('Name')
    DKSalaries = DKSalaries[['Position','TeamAbbrev']][DKSalaries['Position']=='RP']
    
    replaceTeamNames = {'SF':'SFG'}
    for replaceNamei in range(0,DKSalaries.shape[0]):
        if DKSalaries['TeamAbbrev'][replaceNamei] in replaceTeamNames:
            DKSalaries['TeamAbbrev'][replaceNamei] = replaceTeamNames[DKSalaries['TeamAbbrev'][replaceNamei]]
    
    teamList = DKSalaries['TeamAbbrev'].unique().tolist()
    
    pitcherList = DKSalaries.index.tolist()
    statsList = ['IP','wOBA','Hard%','BB%','K%','SLG','GB%','xFIP']
    DKSalaries = populatePitcherStats(statsList,pitcherList,DKSalaries,pitching_2019_L,pitching_2019_R)
    
    pitchRearrangeColumns = ['TeamAbbrev','IP_L','wOBA_L','Hard%_L','BB%_L','K%_L','SLG_L','GB%_L','xFIP_L','IP_R','wOBA_R','Hard%_R','BB%_R','K%_R','SLG_R','GB%_R','xFIP_R']
    DKSalaries = DKSalaries[pitchRearrangeColumns]
    
    bullpenDF = pd.DataFrame()
    for teami in teamList:
        bullpenDF[teami] = DKSalaries[DKSalaries['TeamAbbrev']==teami].mean(skipna = True)
    bullpenDF = bullpenDF.transpose()
    
    for bullpenStati in bullpenDF.columns.tolist():
        if bullpenStati == 'K%_L' or bullpenStati == 'K%_R' or bullpenStati == 'GB%_L' or bullpenStati == 'GB%_R':
            bullpenDF[bullpenStati] = bullpenDF[bullpenStati].rank(na_option='bottom',ascending=False)
        else:
            bullpenDF[bullpenStati] = bullpenDF[bullpenStati].rank(na_option='bottom',ascending=True)
    
    #Average Ranked Stats by Handedness
    bullpenDF['vsL'] = bullpenDF.loc[: , "wOBA_L":"xFIP_L"].mean(axis=1)
    bullpenDF['vsR'] = bullpenDF.loc[: , "wOBA_R":"xFIP_R"].mean(axis=1)
    bullpenDF = bullpenDF[['vsL','vsR']]
    return bullpenDF








        