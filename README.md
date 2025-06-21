# BC Wildfire Predictive Model

## Background and Overview
In recent decades, wildfires have caused widespread environmental damage, economic loss, and displacement of communities across many regions, including British Columbia. To prevent and mitigate the impacts of wildfires, many valuable studies have been conducted in the past. The goal of this project is to develop a predictive model that estimates wildfire risk using historical climate data and location. By analyzing patterns in past wildfires, weather conditions, and other environmental factors, the model aims to identify areas at higher risk. 

Insights and recommendations will provided on these areas:
- **Model Accuracy**: evaluation of each model and its accuracy based on a selection of metrics.
- **Feature Importance**: an analysis of the most important features based on the most accurate model.
- **Partial Independence**: an analysis of the potential influence of the most important features on the predicted probability of a fire.
  
## Data Sources
- *Canada’s National Forestry Database*. This was used to analyze historical trends on burned areas and fire occurrences. It is relevant to provide an appropriate 
overview of the situation in BC. 
- *National Resources Canada*. This website contained fire data from 2000 to 2024 in the form of hotspots. Each hotspot data file contains information on where 
and when each fire occurred. It provided a starting point to understanding fire characteristics. From the same website, data was obtained on the BC area fuel type 
characteristics that were classified into different types. As a result, the conditions of which a fire occurred were able to be identified along with the understanding of which types are more susceptible to fires and which ones are not as susceptible.
-  *ERA5 Monthly Data*. This dataset contains the average monthly climate data in the form of spatial layers.

## Data Transformation Overview
Through  PyGIS, the locations of each BC fire hotspot were extracted, then grouped by month and year. These points were given a ‘Fire’ label of 1. Random generated 
points were generated to represent locations without fires which were classified by the ‘Fire’ label of 0. To ensure appropriate sampling, the number of randomly generated points was made to be equal to the number of fire hotspots that month. On months without fires, they were based on the monthly average number of fire hotspots in that year. The climate data was clipped to BC along with the fuel type data to make separate layers. Each point was sampled, quantifying the climate characteristics and fuel type of each point based on its location. These values along with the latitudes and longitudes of each point were combined to make a comma-separated file which was used for modeling.

Here are the list of variables:
- *2-metre temperature (K)*. The air temperature 2 meters above ground level. High temperatures dry out vegetation, making it more flammable and increasing fire risk.
d2m – dewpoint 
temperature (K) 
Temperature at which air 
becomes saturated with 
moisture (dewpoint) 
Lower dewpoints 
indicate drier air, which 
helps vegetation dry out 
and become more 
ignitable 
10 U & 10 V wind (m) East-west and north
south wind components 
measured at 10 meters 
height 
Wind drives fire to 
spread, oxygen supply, 
and can carry embers 
over long distances 
Tp - Total Precipitation 
(m) 
Total rainfall  Lack of rain leads to dry 
conditions and fuel 
buildup, increasing fire 
potential 
Fuel type The type of vegetation or 
material that can burn 
on the ground 
Different fuels ignite and 
burn at different rates, 
affecting how a fire 
spread 
Leaf Area Index (lai_hv) Amount of leaf coverage 
per unit area, 
representing vegetation 
Higher LAI means more 
available fuel and more 
intense, longer-lasting 
density 
Analysis 
f
 ires
## Executive Summary

## Insights

## Recommendations
