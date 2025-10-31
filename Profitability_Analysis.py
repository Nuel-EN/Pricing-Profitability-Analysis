# -*- coding: utf-8 -*-
"""
Created on Fri Oct 31 22:45:40 2025

@author: Nuel
"""

# ====================================================
# Dash App: Product Pricing & Profitability Dashboard
# ====================================================

import zipfile
import pandas as pd
import dash
from dash import dcc, html, dash_table, Input, Output
import plotly.express as px

import os
# ---------------------------
# Load data from ZIP archive
# ---------------------------
df = pd.read_csv('product_10000.csv')

# ---------------------------
# Data preparation
# ---------------------------
df['profit'] = df['price'] - df['cost']
df['margin_pct'] = (df['profit'] / df['price']) * 100

category_summary = (
    df.groupby(['category', 'subcategory'])
      .agg({
          'product_id': 'count',
          'brand': pd.Series.nunique,
          'price': 'mean',
          'cost': 'mean',
          'profit': 'mean',
          'margin_pct': 'mean'
      })
      .rename(columns={
          'product_id': 'num_products',
          'brand': 'num_brands',
          'price': 'avg_price',
          'cost': 'avg_cost',
          'profit': 'avg_profit',
          'margin_pct': 'avg_margin_%'
      })
      .reset_index()
      .round(2)
)

# ---------------------------
# Initialize Dash app
# ---------------------------
app = dash.Dash(__name__)
app.title = "Product Pricing & Profitability Dashboard"

# ---------------------------
# Layout
# ---------------------------
app.layout = html.Div([
    html.H1("📊 Product Pricing & Profitability Analysis", style={'textAlign': 'center'}),

    html.Div([
        html.Label("Select Category:"),
        dcc.Dropdown(
            id='category-dropdown',
            options=[{'label': cat, 'value': cat} for cat in sorted(df['category'].unique())],
            value=sorted(df['category'].unique())[0],
            clearable=False
        )
    ], style={'width': '40%', 'margin': 'auto'}),

    html.Br(),

    # KPI Cards
    html.Div([
        html.Div([
            html.H4("Total Products", style={'textAlign': 'center', 'color': '#555'}),
            html.H2(id='kpi-products', style={'textAlign': 'center', 'color': '#0074D9'})
        ], className='kpi-card'),

        html.Div([
            html.H4("Total Profit", style={'textAlign': 'center', 'color': '#555'}),
            html.H2(id='kpi-profit', style={'textAlign': 'center', 'color': '#2ECC40'})
        ], className='kpi-card'),

        html.Div([
            html.H4("Average Margin (%)", style={'textAlign': 'center', 'color': '#555'}),
            html.H2(id='kpi-margin', style={'textAlign': 'center', 'color': '#FF851B'})
        ], className='kpi-card'),

        html.Div([
            html.H4("Number of Brands", style={'textAlign': 'center', 'color': '#555'}),
            html.H2(id='kpi-brands', style={'textAlign': 'center', 'color': '#B10DC9'})
        ], className='kpi-card'),
    ], style={'display': 'flex', 'justifyContent': 'space-around', 'margin': '20px 0'}),

    # Summary Table
    html.H3("Category & Subcategory Summary", style={'textAlign': 'center'}),
    dash_table.DataTable(
        id='summary-table',
        columns=[{'name': i, 'id': i} for i in category_summary.columns],
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'center'},
    ),

    html.Br(),

    # Plots
    html.Div([
        dcc.Graph(id='avg-price-plot'),
        dcc.Graph(id='price-distribution-plot'),
        dcc.Graph(id='margin-subcat-plot'),
        dcc.Graph(id='cost-vs-price-plot'),
        dcc.Graph(id='brand-count-plot')
    ])
])

# ---------------------------
# Callbacks for interactivity
# ---------------------------
@app.callback(
    [Output('summary-table', 'data'),
     Output('avg-price-plot', 'figure'),
     Output('price-distribution-plot', 'figure'),
     Output('margin-subcat-plot', 'figure'),
     Output('cost-vs-price-plot', 'figure'),
     Output('brand-count-plot', 'figure'),
     Output('kpi-products', 'children'),
     Output('kpi-profit', 'children'),
     Output('kpi-margin', 'children'),
     Output('kpi-brands', 'children')],
    [Input('category-dropdown', 'value')]
)
def update_dashboard(selected_category):
    dff = df[df['category'] == selected_category]
    summary = category_summary[category_summary['category'] == selected_category]

    # --- KPIs ---
    total_products = len(dff)
    total_profit = dff['profit'].sum()
    avg_margin = dff['margin_pct'].mean()
    num_brands = dff['brand'].nunique()

    # Format KPIs for display
    kpi_products = f"{total_products:,}"
    kpi_profit = f"${total_profit:,.2f}"
    kpi_margin = f"{avg_margin:.2f}%"
    kpi_brands = f"{num_brands:,}"

    # --- Plot 1: Average Price by Subcategory ---
    fig1 = px.bar(
        dff.groupby('subcategory', as_index=False)['price'].mean(),
        x='subcategory', y='price', color='subcategory',
        title=f'Average Price by Subcategory — {selected_category}'
    )

    # --- Plot 2: Price Distribution per Subcategory ---
    fig2 = px.box(
        dff, x='subcategory', y='price', color='subcategory',
        title=f'Price Distribution per Subcategory — {selected_category}'
    )

    # --- Plot 3: Average Profit Margin by Subcategory ---
    fig3 = px.bar(
        dff.groupby('subcategory', as_index=False)['margin_pct'].mean(),
        x='subcategory', y='margin_pct', color='subcategory',
        title=f'Average Profit Margin by Subcategory — {selected_category}'
    )

    # --- Plot 4: Cost vs Price Scatterplot ---
    fig4 = px.scatter(
        dff, x='cost', y='price', color='brand',
        title=f'Cost vs Price by Brand — {selected_category}',
        hover_data=['subcategory', 'brand']
    )
    fig4.add_shape(type="line",
                   x0=dff['cost'].min(), y0=dff['cost'].min(),
                   x1=dff['price'].max(), y1=dff['price'].max(),
                   line=dict(color="gray", dash="dash"))

    # --- Plot 5: Brand Count per Subcategory ---
    brand_counts = dff.groupby('subcategory')['brand'].nunique().reset_index(name='brand_count')
    fig5 = px.bar(
        brand_counts, x='subcategory', y='brand_count', color='subcategory',
        title=f'Number of Brands per Subcategory — {selected_category}'
    )

    return (summary.to_dict('records'),
            fig1, fig2, fig3, fig4, fig5,
            kpi_products, kpi_profit, kpi_margin, kpi_brands)

# ---------------------------
# Run the app
# ---------------------------
#if __name__ == '__main__':
 #   app.run(debug=False)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))  # Use Render's port or default 8050 locally
    app.run_server(host='0.0.0.0', port=port, debug=True)


