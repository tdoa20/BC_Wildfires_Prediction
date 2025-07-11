# BC Wildfire Predictive Model

## Background and Overview
In recent decades, wildfires have caused widespread environmental damage, economic loss, and displacement of communities across many regions, including British Columbia. To prevent and mitigate the impacts of wildfires, many valuable studies have been conducted in the past. The goal of this project is to develop a predictive model that estimates wildfire risk using historical climate data and location. By analyzing patterns in past wildfires, weather conditions, and other environmental factors, the model aims to identify areas at higher risk. 

Insights and recommendations will provided on these areas:
- **Model Accuracy**: evaluation of each model and its accuracy based on a selection of metrics.
- **Feature Importance**: an analysis of the most important features based on the most accurate model.
- **Partial Independence**: an analysis of the potential influence of the most important features on the predicted probability of a fire.
  
## Data Sources
- *National Resources Canada*. This website contained fire data from 2000 to 2024 in the form of hotspots. Each hotspot data file contains information on where and when each fire occurred. It provided a starting point to understanding fire characteristics. From the same website, data was obtained on the BC area fuel type characteristics that were classified into different types. As a result, the conditions of which a fire occurred were able to be identified along with the understanding of which types are more susceptible to fires and which ones are not as susceptible. The link to the dataset can be found <a href = "https://cwfis.cfs.nrcan.gc.ca/downloads/hotspots/archive/">here.</a>
-  *ERA5 Monthly Data*. This dataset contains the average monthly climate data in the form of spatial layers. The dataset only provides values at the 00:00 UTC time frame. As a result, we must assume that variables such as dew point temperature and air temperature are representative of the broader daily and regional conditions. However, users should be aware that this introduces limitations and are encouraged to explore alternative or higher resolution datasets to improve accuracy and granularity of the analysis. The link to the dataset can be found <a href = "https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-monthly-means?tab=overview">here.</a>

## Executive Summary
### Overview of Findings
Out of all models, it was discovered that the random forest model was the most accurate. It had a high sensitivity, but a lower precision and accuracy. This highlights the increased ability to detect fires, but its potential to predict certain fires that are not present. The temperature (dewpoint and 2-metre temperature) and precipitation were the 3 most important. 

<img src="https://github.com/tdoa20/BC_Wildfires_Prediction/blob/b742e31bf7edbab432ce6bd2f61ec5db87a076fe/Screenshot%202025-07-02%20193456.png" width="520" height="200">
Based on the partial independence plots below, increases in the 2-metre temperature corresponded to increases in the average fire probability, but increases in the 2-metre dewpoint temperature and total precipitation generally had the opposite effect on the average fire probability.
<p>
  <img src="https://github.com/tdoa20/BC_Wildfires_Prediction/blob/b742e31bf7edbab432ce6bd2f61ec5db87a076fe/2m_temp_RF_Plot.png" width="320" height="275">
  <img src="https://github.com/tdoa20/BC_Wildfires_Prediction/blob/b742e31bf7edbab432ce6bd2f61ec5db87a076fe/2m_dewpoint_temp_RF_plot.png" width="320" height="275">
  <img src="https://github.com/tdoa20/BC_Wildfires_Prediction/blob/b742e31bf7edbab432ce6bd2f61ec5db87a076fe/Total_Precipitation_RF_Plot.png" width="320" height="275">
</p>

### Recommendations
These models can be used to make forecasts based on the initial data points and then monitor certain areas that have a higher risk of fires. It is important to monitor the 2-metre temperature, 2-metre dewpoint temperature, and total precipitation values daily to detect areas with higher risks of fires. Through this, wildfire services and local utilities are able to adjust their operations and implement different strategies proactively to lower the impact of wildfires on the environment and consequently the property damages.

## Data Transformation Overview
Through  PyGIS, the locations of each BC fire hotspot were extracted, then grouped by month and year. These points were given a ‘Fire’ label of 1. Random generated points were generated to represent locations without fires which were classified by the ‘Fire’ label of 0. To ensure appropriate sampling, the number of randomly generated points was made to be equal to the number of fire hotspots that month. On months without fires, they were based on the monthly average number of fire hotspots in that year. The climate data was clipped to BC along with the fuel type data to make separate layers. Each point was sampled, quantifying the climate characteristics and fuel type of each point based on its location. These values along with the latitudes and longitudes of each point were combined to make a comma-separated file which was used for modeling.

In earlier years, on months with fires, the number of randomly generated points was equal to the number of fire hotspots, but in later years, QGIS was unable to generate the appropriate number of non-fire points. This ended up skewing the data to have more fire hotspots than non-fire generated points. This was due to a limit placed in the code to ensure adequate processing time. This limit can be avoided using a system with greater processing power.

The climate data cleaning script can be found <a href = "https://github.com/tdoa20/BC_Wildfires_Prediction/blob/44c98063cbf2e4c3ce0c18c788f1432d03e807dd/Climate_extraction_loop.py">here.</a>


The point data cleaning script can be found <a href = "https://github.com/tdoa20/BC_Wildfires_Prediction/blob/533ff16e2859b235955be24ba8b251f09169bf0c/Spatial_formatting_loop.py">here.</a>

Here are the list of variables:
- *2-metre temperature (K)*. The air temperature 2 metres above ground level. High temperatures dry out vegetation, making it more flammable and increasing fire risk.
– *2-metre dewpoint temperature (K)*. The temperature at which air becomes saturated with moisture (dewpoint). Lower dewpoints indicate drier air, which helps vegetation dry out and become more ignitable.
- *10 U & 10 V wind (m)*. This is a measure of the fire spread direction & speed. It is divided into East-west (V) and north-south (U) wind components measured at a height of 10 metres. Wind drives fire to spread, oxygen supply, and can carry embers over long distances. These components were used to derive the windspeed.
- *Total Precipitation (m)*. Average Total rainfall. Lack of rain leads to dry conditions and fuel buildup, increasing fire potential.
- *Fuel type*. The type of vegetation or material that can burn on the ground. Different fuels ignite and burn at different rates, affecting how a fire spreads.
- *Leaf Area Index*. The amount of leaf coverage per unit area, representing vegetation. A higher LAI means more available fuel and more intense, longer-lasting fires. 


## Insights
### Accuracy
This table shows the 3 models that were run on the data. The most accurate model was determined based on these metrics.
| Model      | AUC | Root Mean Squared Error (RMSE)  | Accuracy | Precision | Sensitivity (recall) |
| ----------- | ----------- | ----------- | ----------- | ----------- | ----------- |
| Logistic regression | 0.8679  | 0.3479 | 0.8789 | 0.9012 | 0.9596 |
| XGBoost   | 0.9679   | 0.2633   | 0.93066   | 0.9425   | 0.9762   |
| **Random forest**   | **0.9883**   | **0.1281**   | **0.9840**   | **0.9890**   | **0.9913**   |

- In all models, the sensitivity was higher than precision, which is indicative of its increased ability to detect fires. This could also be dependent on the sample as 83.1% of the test data consisted of fire points. 
- The logistic regression model was the least accurate according to the AUC and RMSE with a value of 0.8679 and 0.3479 respectively. It generally had the lowest values when it came to accuracy, sensitivity, and recall. The AUC was considerably lower than that of the XGBoost and Random Forest model. 
- The random forest model was the most accurate out of the 3, having the highest AUC, accuracy, precision sensitivity and the lowest RMSE.

#### Confusion Matrix
This matrix highlights the accuracy of the Random Forest model chosen.
|       | Predicted Non-Fire Points | Predicted Fire Points      |
| ----------- | ----------- | ----------- |
| **Actual Non-Fire Points**| 122655 | 7025 |
| **Actual Fire Points** | 5589 | 633838 |

- Out of the 639427 total tested fire points, the random forest model managed to predict 633838 of them accurately.
- Out of the 129680 non-fire points, it managed to predict only 122655 of them accurately.
- The number of fire points predicted inaccurately was less than 1500 more at 7025 than the inaccurately predicted non-fire points at 5589 even though there were almost 5 times as many fire points than non-fire points.
- This reinforces the observation that the model is better at detecting areas with fires than areas without fires. 


#### Map comparison 
This outlines the comparison between the predicted fire points and the actual fire points in August 2024 using the random forest model. The map on the left highlights the actual fire points that were predicted correctly, and the map on the right highlights the fire points that were predicted incorrectly.
<br><img src = "https://github.com/tdoa20/BC_Wildfires_Prediction/blob/28dbfda8fbb1d07c6b195ddffaf498327b91f4bb/Screenshot%202025-05-25%20135043.png"></br>

Out of the 74,819 actual fire points, it managed to predict 74746 of them and failed to predict 73 of them. This highlights the heightened ability of the model to detect fires. 

### Feature importance
This plot highlights the most important features of the random forest model in descending order.
<img src="https://github.com/tdoa20/BC_Wildfires_Prediction/blob/b742e31bf7edbab432ce6bd2f61ec5db87a076fe/Screenshot%202025-07-02%20193456.png" width="520" height="200">

- The most important features were 2m-temperature (30%), 2-metre dewpoint temperature (21%), and total precipitation (19%). These 3 features account for almost 70 percent of the prediction.  
- The ordering of the most important features matched the model made by Norton (2024), except for the 2-metre temperature being rated as the 2nd most important based on this rather than the 2nd least important. 
- The most important fuel type for the random forest was 119 (non fuel). This type refers to alpine areas with patchy vegetation that would not normally cause fires.

### Partial Independence Plot Patterns
To understand the impact of these variables on the random forest model in more detail, we made partial independence plots based on the top 3 features ranked by importance.

#### 2-metre temperature

  <img src="https://github.com/tdoa20/BC_Wildfires_Prediction/blob/b742e31bf7edbab432ce6bd2f61ec5db87a076fe/2m_temp_RF_Plot.png" width="320" height="275">
  
- From 245 K to 282 K, the average probability remains at 13 percent. Then it decreases from 13% to 7% from 282 to 284 K.
- From 284 to 285 K, it increases by 7% to 14% and continues to generally rise from there.  
- At lower temperatures, there is practically no effect but at higher ones, there is a positive relationship to fire risk.
- This pattern is understandable as high temperatures cause vegetation to dry out, making it more flammable and increasing fire risk. 

#### 2-metre dewpoint temperature
  <img src="https://github.com/tdoa20/BC_Wildfires_Prediction/blob/b742e31bf7edbab432ce6bd2f61ec5db87a076fe/2m_dewpoint_temp_RF_plot.png" width="320" height="275">

- 2m-dewpoint temperature has an opposite effect on the average probabilities.  
- From 241 K to 276 K, it remains at a consistent level of 19%.
- At 277 K, it decreases to 14% and generally exhibits the same trend.
- This is understandable as higher dewpoints indicate more humid air, which decreases the potential for ignition for vegetation. 

#### Total Precipitation
  <img src="https://github.com/tdoa20/BC_Wildfires_Prediction/blob/b742e31bf7edbab432ce6bd2f61ec5db87a076fe/Total_Precipitation_RF_Plot.png" width="320" height="275">

- The average probabilities generally decrease to a level with an increase in  total precipitation.
- At extremely low levels ranging from almost 0 to 0.003177 metres, the probabilities fluctuate between 14 and 18 percent generally decreasing in the process.
- At values higher than that, they stay at a consistent level of around 14 percent. 

### Key Findings
When analysing the 3 models, the random forest model was deemed to be the most accurate based on the metrics chosen. The 2-metre temperature, 2-metre dewpoint temperature, and total precipitation were the most important features in order for the random forest model. 2-metre temperature increases generally correspond to increases in fire probability for both models. The opposite relationship is seen for the 2-metre dewpoint temperature. In the geospatial model, total precipitation increases correspond to decreases in the fire probability.

## Recommendations
According to the analysis, it is important to monitor 2-metre temperature values daily with a drone to capture places that are likely to hit the 280 K mark for the 2-metre temperature as the highest average probability jumps occur in that range. The 2-metre dewpoint temperatures up to 280 K should also be monitored as average fire probabilities are higher. Finally, areas with low precipitation totals should be tracked as on average, they have a higher chance of fires.

### Costs 
Due to the large number of data points collected, one would need to purchase a device with a high processing power to run the code accurately whilst being efficient in the run time. One would need specific high-end drones which specialise in climate surveillance. These can cost up to $22,000 to buy and use depending on the area covered in surveillance. Time would also need to be invested in collecting data. Finally, there will be implementation costs that would be associated with testing out the different strategies in search for the right response based on the risk. 

### Benefits 
Despite the costs, by looking out for certain details, and monitoring the risk, wildfire services and local utilities are able to take certain measures proactively to limit the impact of wildfires on infrastructure and the environment.  

## Conclusion
With the right model, one can accurately predict the occurrence of fires. This can be further implemented with necessary forecasting on the relevant explanatory variables to detect areas with a high risk of fires one season ahead. Although it is 
costly to implement due to the resources required, it will ultimately save lives and reduce the impact wildfires have on the environment and property. 
