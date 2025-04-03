from flask import Flask, render_template
from google.cloud import bigquery
import plotly.express as px
import pandas as pd

app = Flask(__name__)

# Initialize BigQuery client
client = bigquery.Client()


@app.route('/api/sales-analysis-umg/')
def sales_analysis():
    # Define the query
    query = """
    WITH census_sales AS (
      SELECT
        SAFE_CAST(REGEXP_EXTRACT(string_field_1, r'(\\d{4})') AS INT) AS year,
        CASE
          WHEN REGEXP_CONTAINS(string_field_1, r'1st') THEN 1 
          WHEN REGEXP_CONTAINS(string_field_1, r'2nd') THEN 2 
          WHEN REGEXP_CONTAINS(string_field_1, r'3rd') THEN 3 
          WHEN REGEXP_CONTAINS(string_field_1, r'4th') THEN 4 
          ELSE NULL
        END AS quarter,
        SAFE_CAST(REGEXP_REPLACE(REGEXP_REPLACE(string_field_2, r'[^0-9.]', ''), r',', '') AS FLOAT64) AS total_retail_sales,
        SAFE_CAST(REGEXP_REPLACE(REGEXP_REPLACE(string_field_3, r'[^0-9.]', ''), r',', '') AS FLOAT64) AS total_ecommerce_sales
      FROM `umg-test-project.q4_retail_sales_data.q4_sales_data_census`
      WHERE
        REGEXP_CONTAINS(REGEXP_REPLACE(REGEXP_REPLACE(string_field_2, r'[^0-9.-]', ''), r',', ''), r'^-?\\d+(\\.\\d+)?$') 
        AND REGEXP_CONTAINS(REGEXP_REPLACE(REGEXP_REPLACE(string_field_3, r'[^0-9.-]', ''), r',', ''), r'^-?\\d+(\\.\\d+)?$') 
        AND SAFE_CAST(REGEXP_EXTRACT(string_field_1, r'(\\d{4})') AS INT) BETWEEN 2023 AND 2024
    ),
    ecommerce_sales AS (
      SELECT
        EXTRACT(YEAR FROM created_at) AS year,
        EXTRACT(QUARTER FROM created_at) AS quarter,
        SUM(sale_price) AS total_ecommerce_sales 
      FROM `bigquery-public-data.thelook_ecommerce.order_items`
      WHERE EXTRACT(YEAR FROM created_at) BETWEEN 2023 AND 2024
      GROUP BY year, quarter
    )
    SELECT
      c.year,
      c.quarter,
      c.total_retail_sales,
      c.total_ecommerce_sales AS census_ecommerce_sales,
      e.total_ecommerce_sales AS bigquery_ecommerce_sales,
      (c.total_ecommerce_sales / c.total_retail_sales) * 100 AS census_ecommerce_penetration_rate,
      e.total_ecommerce_sales - c.total_ecommerce_sales AS ecommerce_sales_difference,
      IFNULL(
        (c.total_ecommerce_sales - LAG(c.total_ecommerce_sales) OVER (PARTITION BY c.year ORDER BY c.quarter)) / LAG(c.total_ecommerce_sales) OVER (PARTITION BY c.year ORDER BY c.quarter) * 100, 0) AS census_ecommerce_growth_rate,
      IFNULL(
        (e.total_ecommerce_sales - LAG(e.total_ecommerce_sales) OVER (PARTITION BY e.year ORDER BY e.quarter)) / LAG(e.total_ecommerce_sales) OVER (PARTITION BY e.year ORDER BY e.quarter) * 100, 0) AS bigquery_ecommerce_growth_rate,
      (e.total_ecommerce_sales / c.total_ecommerce_sales) * 100 AS ecommerce_sales_benchmark
    FROM
      census_sales c
    LEFT JOIN
      ecommerce_sales e
    ON
      c.year = e.year AND c.quarter = e.quarter
    ORDER BY
      c.year, c.quarter;
    """

    # Execute the query
    query_job = client.query(query)
    sales_data = [dict(row) for row in query_job]

    # Convert to DataFrame
    df = pd.DataFrame(sales_data)

    # Renaming columns for better readability
    df.rename(columns={
        'census_ecommerce_sales': 'Census E-commerce Sales',
        'bigquery_ecommerce_sales': 'BigQuery E-commerce Sales',
        'census_ecommerce_growth_rate': 'Census',
        'bigquery_ecommerce_growth_rate': 'BigQuery',
        'total_retail_sales': 'Total Retail Sales'
    }, inplace=True)

    df_2024 = df[df['year'] == 2024]
    df_2024_melted = df_2024.melt(id_vars=['quarter'],
                                  value_vars=['Census E-commerce Sales', 'BigQuery E-commerce Sales',
                                              'Total Retail Sales'],
                                  var_name='Sales Type', value_name='Sales')
    quarterly_sales_fig = px.line(df_2024_melted, x='quarter', y='Sales', color='Sales Type', title='Quarterly Sales Trend in 2024')

    # Create a Plotly line chart
    line_fig = px.line(df, x='quarter', y='BigQuery E-commerce Sales', color='year', title='E-commerce Sales Over Time')

    # Create a Plotly bar chart for Census vs BigQuery sales
    df_melted = df.melt(id_vars=['year', 'quarter'],
                        value_vars=['Census E-commerce Sales', 'BigQuery E-commerce Sales'],
                        var_name='source', value_name='sales')

    bar_fig = px.bar(df_melted, x='quarter', y='sales', color='source', barmode='group',
                     facet_col='year', title='Census vs BigQuery E-Commerce Sales')

    # Create a Plotly bar chart for 2024 growth rates
    df_2024 = df[df['year'] == 2024]
    df_2024_melted = df_2024.melt(id_vars=['quarter'],
                                  value_vars=['Census', 'BigQuery'],
                                  var_name='source', value_name='growth_rate')
    growth_fig = px.bar(df_2024_melted, x='quarter', y='growth_rate', color='source', barmode='group',
                        title='2024 E-Commerce Sales Growth Comparison')

    # Customizing layout to adjust font sizes
    for fig in [quarterly_sales_fig, line_fig, bar_fig, growth_fig]:
        fig.update_layout(
            title_font=dict(size=24, family='Lucida Console, Monospace', color='dark blue'),
            xaxis_title_font=dict(size=14, family='Lucida Console, Monospace', color='dark blue'),
            yaxis_title_font=dict(size=14, family='Lucida Console, Monospace', color= 'dark blue'),
            legend=dict(
                font=dict(size=12, family='Lucida Console, Monospace', color='dark blue')
            )
        )

    # Convert the Plotly figures to HTML
    quarterly_sales_html = quarterly_sales_fig.to_html(full_html=False)
    line_graph_html = line_fig.to_html(full_html=False)
    bar_graph_html = bar_fig.to_html(full_html=False)
    growth_graph_html = growth_fig.to_html(full_html=False)

    # Render the HTML template with the charts
    return render_template('charts.html', quarterly_sales_html=quarterly_sales_html,line_graph_html=line_graph_html, bar_graph_html=bar_graph_html,
                           growth_graph_html=growth_graph_html)

if __name__ == '__main__':
    app.run(debug=True)
