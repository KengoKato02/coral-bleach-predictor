[Taken From NOAA Data Descriptions](https://coralreefwatch.noaa.gov/product/vs/description.php#ascii)

Averaged Maximum Monthly Mean (MMM):
The maximum value across the twelve average monthly mean daily global 5km 'CoralTemp' SSTs for pixels contained in a Regional Virtual Station. This value is represented as a dashed light blue line on the time series graphs. The bleaching threshold (solid light blue line) is 1 degree Celsius greater than this MMM value.

Averaged Monthly Mean (Jan-Dec):
The average of the monthly mean daily global 5km 'CoralTemp' SSTs for pixels contained in a Regional Virtual Station. These values are represented as light blue "+" symbols on the time series graphs. The maximum of these values represents the MMM for a particular Regional Virtual Station.

First Valid DHW and BAA date:
The Degree Heating Week (DHW) product for Regional Virtual Stations is an accumulation of the 90th percentile Coral Bleaching HotSpot values within each station. Because it is an accumulation over a 12-week period, there cannot be a DHW value until 12 weeks of HotSpots have occurred. Therefore the first valid DHW date is later than the first valid SST and HotSpot date. The same goes for the Bleaching Alert Area product, which has a slightly later start date, due to the fact that it is a 7-day maximum composite.

The last line of the header describes the time series data that follows. There are 10 fields in each record described in detail below:

YYYY, MM, DD:
These are the year, month, and day, respectively, of the data.

SST_MIN and SST_MAX:
The minimum and maximum daily global 5km 'CoralTemp' SST value for pixels contained in a Regional Virtual Station. This shows the dynamic range in SST values within a Regional Virtual Station and is a reference for the size and variability of oceanographic conditions of a station.

SST@90th_HS:
The daily SST value where the Coral Bleaching HotSpot value is equal to the 90th percentile HotSpot value for pixels contained in a Regional Virtual Station. This acts as a moving pixel within a region that is free to migrate with each data update. It follows thermal stress as indicated by the HotSpot value for that day. These values are represented on the time series graphs as a solid dark blue line that falls within the SST_MIN and SST_MAX range. This value is used in the information balloons in the Google Maps and Google Earth interfaces.

SSTA@90th_HS:
The daily global 5km SST Anomaly value where the Coral Bleaching HotSpot value is equal to the 90th percentile HotSpot value for pixels contained in a Regional Virtual Station. This acts as a moving pixel within a region that is free to migrate with each data update. It follows temperature anomalies as indicated by the Coral Bleaching HotSpot value for that day. This value is used in the information balloons in the Google Maps and Google Earth interfaces.

90th_HS>0:
The daily 90th percentile Coral Bleaching HotSpot value (positive only) for pixels contained in a Regional Virtual Station. This acts as a moving pixel within a region that is free to migrate with each data update. This value is used in the information balloons in the Google Maps and Google Earth interfaces. This value is accumulated over time to calculate the Degree Heating Week and Bleaching Alert Area values for each Regional Virtual Station.

DHW_from_90th_HS>1:
The daily global 5km DHW value calculated by accumulating daily 90th percentile Coral Bleaching HotSpot values (greater than 1) for pixels contained in a Regional Virtual Station. This value is used in the information balloons in the Google Maps and Google Earth interfaces. This value is represented as a solid red line on the time series graphs.

BAA_7day_max:
The daily global 5km Bleaching Alert Area single-day value is derived from the 90th percentile Coral Bleaching HotSpot and DHW pair. This follows CRW's existing algorithm, but uses the unique 90th percentile Coral Bleaching HotSpot and DHW values for each Regional Virtual Station. From the Bleaching Alert Area single-day values, the rolling Bleaching Alert Area (7-day maximum) composite value is calculated and used to color the area below the DHW trace on the time series graph. These alert values are used to change the Bleaching Heat Stress Gauges and send automated alerts to Satellite Bleaching Alert Email System subscribers. A value of 0 = No Stress, 1 = Bleaching Watch, 2 = Bleaching Warning, 3 = Alert Level 1, and 4 = Alert Level 2.