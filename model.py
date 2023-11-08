import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error
from lifetimes import BetaGeoFitter
from lifetimes import GammaGammaFitter
from lifetimes.utils import calibration_and_holdout_data
from lifetimes.utils import summary_data_from_transaction_data
import csv
import datetime
import seaborn as sns
import datetime as dt
from graph import plot_calibration_purchases_vs_holdout_purchases


def process_csv(filename, month):
    ##################################################################
    # DATA CLEANING #
    ##################################################################
    df = pd.read_csv(filename)
    df.dropna(inplace=True)
    df = df[~df['Quantity'] < 0]

    df['InvoiceNo'] = df['InvoiceNo'].astype('str')
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['CustomerID'] = df['CustomerID'].astype('str')
    df['Description'] = df['Description'].astype('str')
    df['StockCode'] = df['StockCode'].astype('str')

    df = df[~df['InvoiceNo'].str.startswith('c')].reset_index(drop = True)
    df['Monetary'] = df['Quantity'] * df['UnitPrice']

    df_rfmt = summary_data_from_transaction_data(transactions = df,
                                            customer_id_col = 'CustomerID',
                                            datetime_col = 'InvoiceDate',
                                            monetary_value_col = 'Monetary')

    diff_time = df['InvoiceDate'].max() - df['InvoiceDate'].min()
    end_date_cal = df['InvoiceDate'].min() + dt.timedelta(days=200)
    end_date_obs = end_date_cal + (diff_time - dt.timedelta(days=200))


    ##################################################################
    # TRAIN TEST SPLIT #
    ##################################################################

    df_rfmt_cal = calibration_and_holdout_data(transactions=df,
                                            customer_id_col="CustomerID",
                                            datetime_col = "InvoiceDate",
                                            calibration_period_end=end_date_cal,
                                            observation_period_end= end_date_obs)



    ##################################################################
    # MODEL BUILDING #
    ##################################################################

    #BG/NBD model building
    l2_coefs = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.4, 1.6]
    l2_list = []
    coef_score = {}
    rmse_list = []
    for coef in l2_coefs :
        # Fitting the model using the calibration dataset.
        model = BetaGeoFitter(penalizer_coef=coef)
        model.fit(df_rfmt_cal['frequency_cal'],
            df_rfmt_cal['recency_cal'],
            df_rfmt_cal['T_cal'])
        # Predicting the frequency for the holdout period for all customers.
        pred_freq = pd.DataFrame(model.predict(df_rfmt_cal['duration_holdout'],
                                    df_rfmt_cal['frequency_cal'], df_rfmt_cal['recency_cal'], df_rfmt_cal['T_cal']), columns=['pred_frequency']).reset_index()
        # Merging the two dataframes and dropping NaN values.
        new_df = df_rfmt_cal.reset_index().merge(pred_freq, on='CustomerID').dropna()

        # Computing the rmse score
        rmse_score = np.sqrt(mean_squared_error(new_df['frequency_holdout'],new_df['pred_frequency']))
        l2_list.append(coef)
        rmse_list.append(rmse_score)
        coef_score[coef] = rmse_score


    coef_with_lowest_score = min(coef_score, key=lambda k: coef_score[k])

    model = BetaGeoFitter(penalizer_coef=coef_with_lowest_score)
    model.fit(df_rfmt_cal['frequency_cal'],
            df_rfmt_cal['recency_cal'],
            df_rfmt_cal['T_cal'])

    plot_calibration_purchases_vs_holdout_purchases(model, df_rfmt_cal)

    df_rfmt['predicted_purchases'] = model.conditional_expected_number_of_purchases_up_to_time(180,
                                                                                        df_rfmt['frequency'],
                                                                                        df_rfmt['recency'],
                                                                                        df_rfmt['T'])
    df_rfmt.dropna(inplace=True)
    # Getting rid of negative values.
    df_rfmt = df_rfmt[df_rfmt['monetary_value']>0]



    #Gamma-gamma model building
    gg_model = GammaGammaFitter()
    gg_model.fit(df_rfmt['frequency'], df_rfmt['monetary_value'])

    df_rfmt['pred_monetary'] = gg_model.conditional_expected_average_profit(
            df_rfmt['frequency'],
            df_rfmt['monetary_value'])

    df_rfmt['CLV'] = gg_model.customer_lifetime_value(
        model,
        df_rfmt['frequency'],
        df_rfmt['recency'],
        df_rfmt['T'],
        df_rfmt['monetary_value'],
        time = month,# In months
        )
    
    df_rfmt = df_rfmt.reset_index()
    #output = df_rfmt.to_csv('output\clv_predicted.csv')
    

    ##################################################################
    # Visualise Clusters #
    ##################################################################
    df = df_rfmt
    km_model = KMeans(n_clusters=4)
    km_model.fit(df)
    
    # Creating a new column called cluster whose values are the corresponding cluster for each point.
    df['cluster'] = km_model.labels_


    df_clusters= df.groupby(['cluster'])['CLV']\
                    .agg(['mean', "count"])\
                    .reset_index()

    df_clusters.columns = ["cluster", "avg_CLV", "n_customers"]

    df_clusters['perct_customers'] = (df_clusters['n_customers']/df_clusters['n_customers']\
                                .sum())*100
    df_clusters = df_clusters.sort_values(by = 'avg_CLV', ascending=False)
    cluster_mapping = {
    0: 'Bronze',
    1: 'Diamond',
    2: 'Gold',
    3: 'Silver'
    }

    # Replace the "cluster" column values based on the mapping
    df['customer_category'] = df['cluster'].map(cluster_mapping)

    df_clusters = df_clusters.reset_index(drop=True)

    df_cat = pd.DataFrame(df.groupby(['customer_category'])['CLV']\
                    .agg('mean')).reset_index()


    plt.figure(figsize=(8, 8))


    plots = sns.barplot(x="customer_category", y="CLV", data=df_cat)

    # Iterating over the bars one-by-one
    for bar in plots.patches:
        plots.annotate(format(bar.get_height(), '.2f'),
                    (bar.get_x() + bar.get_width() / 2,
                        bar.get_height()), ha='center', va='center',
                    size=15, xytext=(0, 8),textcoords='offset points')

    plt.xlabel("Customer category", size=14)

    # Setting the label for y-axis
    plt.ylabel("CLV", size=14)

    # Setting the title for the graph
    plt.title("CLV per category")

    plt.savefig('static/my_plot.png')




    ##################################################################
    # Saving file #
    ##################################################################
    output = df_rfmt[["CustomerID", "CLV"]]

    current_datetime = datetime.datetime.now()

    current_date = current_datetime.date()
    current_time = current_datetime.time()

    current_hour = current_time.hour
    current_min = current_time.minute

    output_file = f"{month}_months_CLV_predicted_{current_date}_{current_hour:02}_{current_min:02}.csv"
    output_dir = f"output\{output_file}"
    with open(output_dir, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["CustomerID", 'CLV'])
        for index, row in output.iterrows():
            writer.writerow([row["CustomerID"], row['CLV']])
    
    return output_file



