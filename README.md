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
– *2-metre dewpoint temperature (K)*. The temperature at which air becomes saturated with moisture (dewpoint). Lower dewpoints indicate drier air, which helps vegetation dry out and become more ignitable.
- *10 U & 10 V wind (m)*. This is a measure of the fire spread direction & speed. It is divided into East-west (V) and north-south (U) wind components measured at a height of 10 meters. Wind drives fire to spread, oxygen supply, and can carry embers over long distances.
- *Total Precipitation (m)*. Average Total rainfall. Lack of rain leads to dry conditions and fuel buildup, increasing fire potential.
- *Fuel type*. The type of vegetation or material that can burn on the ground. Different fuels ignite and burn at different rates, affecting how a fire spreads.
- *Leaf Area Index*. The amount of leaf coverage per unit area, representing vegetation. A higher LAI means more available fuel and more intense, longer-lasting fires. 

## Executive Summary
### Overview of Findings
Out of all models, it was discovered that the random forest model was the most accurate. It had a high sensitivity, but a lower precision and accuracy. This highlights the increased ability to detect fires, but its potential to predict certain fires that are not present.

Out of all the features observed in the random forest model, the temperature (dewpoint and 2-metre temperature) and precipitation were the 3 most important. Based on partial independence plots, increases the 2-metre temperature corresponded to increases in the average fire probability, but increases in the 2-metre dewpoint temperature and total 
precipitation generally had the opposite effect on the average fire probability.

## Recommendations
These models can be used to make forecasts based on the initial data points and then monitor certain areas that have a higher risk of fires. It is important to monitor the 2-meter temperature, 2-metre dewpoint temperature, and total precipitation values daily to detect areas with higher risks of fires. Through this, wildfire services and local utilities are able to adjust their operations and implement different strategies proactively to lower the impact of wildfires on the environment and consequently the property damages.

## Insights

## Recommendations
