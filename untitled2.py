#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jul 19 19:24:27 2020

@author: daviddevito
"""

from pybaseball import batting_stats_dkpts
import pandas as pd
import numpy as np

from bs4 import BeautifulSoup
import requests
import matplotlib.pyplot as plt

# Expand limits of printing
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

# LOAD STATS BY HANDEDNESS
batting_2019_B = batting_stats_dkpts(2019, end_season=None, league='all', qual=1, ind=1, handVar='B')
batting_2019_B = batting_2019_B[batting_2019_B['PA'] >= 70]


batting_2019_B = batting_2019_B.set_index('Name')


## CALCULATE DKPTS PER STAT
plateAppearances = batting_2019_B['PA'].values
single = (batting_2019_B['1B'].values)*3
double = (batting_2019_B['2B'].values)*5
triple = (batting_2019_B['3B'].values)*8
homeRun = (batting_2019_B['HR'].values)*10
rbi = (batting_2019_B['RBI'].values)*2
run = (batting_2019_B['R'].values)*2
walk = (batting_2019_B['BB'].values)*2
hbp = (batting_2019_B['HBP'].values)*2
stolenBase = (batting_2019_B['SB'].values)*5

## CALCULATE TOTAL DKPTS
dkptsTotal = single + double + triple + homeRun + rbi + run + walk + hbp + stolenBase

## CALCULATE DKPTS PER PLATE APPEARANCE
dkptsPerPA = dkptsTotal/plateAppearances

batting_2019_B['dkptsPerPA'] = dkptsPerPA


X = batting_2019_B['SB'].values
Y = batting_2019_B['dkptsPerPA'].values

fig=plt.figure()
ax=fig.add_axes([0,0,1,1])
ax.scatter(X, Y, color='r')
#ax.set_xlabel('wOBA')
#ax.set_ylabel('DK Pts per PA')
ax.set_title('DK Pts per PA vs wOBA')
plt.show()



z = np.polyfit(x=X, y=Y, deg=1)
p = np.poly1d(z)
batting_2019_B['trendline'] = p(X)

#ax = batting_2019_B.plot.scatter(x=X, y=Y)
#batting_2019_B.set_index(X, inplace=True)
#batting_2019_B.trendline.sort_index(ascending=False).plot(ax=ax)
#plt.gca().invert_xaxis()


print('y= {0:.4f} x + {1:.4f}'.format(z[0],z[1]))

#y=1.16 x + 70.46



from sklearn.linear_model import LinearRegression



fullX = [batting_2019_B['wOBA'].values,
         batting_2019_B['Hard%'].values,
         batting_2019_B['BB%'].values,
         batting_2019_B['K%'].values,
         batting_2019_B['ISO'].values,
         batting_2019_B['GB%'].values,
         batting_2019_B['wRC+'].values,
         batting_2019_B['SB'].values,
         np.ones(len(batting_2019_B['SB'].values))]
fullX = np.transpose(fullX)

y = batting_2019_B['dkptsPerPA'].values


reg = LinearRegression().fit(fullX, y)

print(reg.coef_)

print(reg.intercept_)

























