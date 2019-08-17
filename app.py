###################################################################################################
# Step 2 - Climate App
#
#   Now that you have completed your initial analysis, design a Flask API based on the queries that
#   you have just developed.
#
#   Routes
#
#       1. `/api/v1.0/precipitation`
#           - Design a query to retrieve the last 12 months of precipitation data and JSONify the results
#       2. `/api/v1.0/stations`
#           - Return a JSON list of stations from the dataset.
#       3. `/api/v1.0/tobs`
#           - Query and return a JSON list of Temperature Observations (tobs) for the previous year
#       4. `/api/v1.0/<start>`
#           - When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` for all following dates
#       5. `/api/v1.0/<start>/<end>`
#           - When given the start and the end date, calculate the `TMIN`, `TAVG`, and `TMAX` 
#               for dates between the start and end date.
###################################################################################################
# import dependencies 
from flask import Flask, jsonify
import datetime as dt
import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()
# Reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def index():
    """List all available api routes."""
    return (
        f"<h1>Step 2 - Climate App</h1>"
        f"Now that I have completed my initial analysis in Jupyter Notebook, this is a Flask API of the queries I have just developed.<br/><br/><br/>"
        f"<h2>Available Routes:</h2>"
        f"<ol><li><a href=http://127.0.0.1:5000/api/v1.0/precipitation>"
        f"JSON list of precipitation amounts by date for the most recent year of data available</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/stations>"
        f"JSON list of weather stations and their details</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/tobs>"
        f"JSON list of the last 12 months of recorded temperatures</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/2017-08-23>"
        f"When given the start date (YYYY-MM-DD), calculates the minimum, average, and maximum temperature for all dates greater than and equal to the start date</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/2016-08-23/2017-08-23>"
        f"When given the start and the end date (YYYY-MM-DD), calculate the minimum, average, and maximum temperature for dates between the start and end date</a></li></ol><br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    ############################################################################################################
    # Design a query to retrieve the last 12 months of precipitation data and JSONify the results
    ############################################################################################################
    
    # Calculate the date 1 year ago from the last data point in the database
    last_date = session.query(func.max(Measurement.date)).scalar() #'2017-08-23'
    date_one_yr_ago_dt = dt.datetime.strptime(last_date, '%Y-%m-%d') - dt.timedelta(days=365) #'2016-08-23'
    date_one_yr_ago = date_one_yr_ago_dt.strftime('%Y-%m-%d')

    # Perform a query to retrieve the data and precipitation scores
    results = session.query(Measurement.date, Measurement.prcp).\
            filter(Measurement.date.between(date_one_yr_ago, last_date),\
                  Measurement.prcp != None).all()

    # Save the query results as a Pandas DataFrame and set the index to the date column
    last_yr_precip_df = pd.DataFrame(results).set_index('date')

    # Sort the dataframe by date
    df2 = last_yr_precip_df.sort_values('date')

    return jsonify(df2.T.to_dict())

@app.route("/api/v1.0/stations")
def stations():
    #######################################################
    # Return a JSON list of stations from the dataset
    #######################################################

    cnxn = engine.connect()
    stations = pd.read_sql('SELECT * FROM station', cnxn)
    stations.set_index('name', inplace=True)

    return jsonify(stations.T.to_dict())

@app.route("/api/v1.0/tobs")
def tobs():
    #######################################################################################################
    # Design a query to retrieve the last 12 months of temperature data and jsonify the results
    #######################################################################################################

    # Calculate the date 1 year ago from the last data point in the database
    last_date = session.query(func.max(Measurement.date)).scalar() #'2017-08-23'
    date_one_yr_ago_dt = dt.datetime.strptime(last_date, '%Y-%m-%d') - dt.timedelta(days=365) #'2016-08-23'
    date_one_yr_ago = date_one_yr_ago_dt.strftime('%Y-%m-%d')

    # Perform a query to retrieve temperatures for the previous year
    results = session.query(Measurement.date, Measurement.tobs).\
                    filter(Measurement.date.between(date_one_yr_ago, last_date)).all()

    # Save the query results as a Pandas DataFrame and set the index to the date column
    last_yr_temp_df = pd.DataFrame(results).set_index('date')

    # Sort the dataframe by date
    df2 = last_yr_temp_df.sort_values('date')

    return jsonify(df2.T.to_dict())

@app.route("/api/v1.0/<start>")
def start(start):
    ##########################################################################################################
    #  When given the start only, calculate `TMIN`, `TAVG`, and `TMAX` for all dates following the start date
    ##########################################################################################################
    
    last_date = session.query(func.max(Measurement.date)).scalar()
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    tmin, tavg, tmax = np.ravel(session.query(*sel).\
                                        filter(Measurement.date.between(start, last_date)).all())
    return (
            f"Minimum, average and maximum temperatures after {start}:<br/><br/>"
            f"TMIN: {tmin:.1f}°F<br/><br/>TAVG: {tavg:.1f}°F<br/><br/>TMAX: {tmax:.1f}°F"
            )

@app.route("/api/v1.0/<start>/<end>")
def startend(start, end):
    #######################################################################################################
    # When given the start and the end date, calculate the `TMIN`, `TAVG`, and `TMAX` 
    # for dates between the start and end date inclusive
    #######################################################################################################
    
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    tmin, tavg, tmax = np.ravel(session.query(*sel).\
                                        filter(Measurement.date.between(start, end)).all())
    return (
            f"Minimum, average and maximum temperatures between {start} and {end}:<br/><br/>"
            f"TMIN: {tmin:.1f}°F<br/><br/>TAVG: {tavg:.1f}°F<br/><br/>TMAX: {tmax:.1f}°F"
            )

if __name__ == "__main__":
    app.run(debug=True)