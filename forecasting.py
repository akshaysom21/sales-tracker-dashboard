import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
import os
warnings.filterwarnings('ignore')

from config import FORECAST_CONFIG


def prepare_data_for_forecast(df, metric='revenue'):

    metric_map = {
        'revenue': ('revenue', 'sum'),
        'orders': ('order_id', 'count'),
        'profit': ('profit', 'sum'),
        'units': ('quantity', 'sum'),
    }

    if metric not in metric_map:
        raise ValueError(f"metric must be one of: {list(metric_map.keys())}")

    col, agg_func = metric_map[metric]

    if agg_func == 'sum':
        daily = df.groupby('date')[col].sum().reset_index()
    else:
        daily = df.groupby('date')[col].count().reset_index()

    daily.columns = ['ds', 'y']
    daily['ds'] = pd.to_datetime(daily['ds'])
    daily = daily.sort_values('ds').reset_index(drop=True)
    daily = daily[daily['y'] > 0]

    print(f"Forecast data prepared for '{metric}':")
    print(f"  Days of data : {len(daily)}")
    print(f"  From : {daily['ds'].min().date()}")
    print(f"  To : {daily['ds'].max().date()}")
    print(f"  Daily average : {daily['y'].mean():,.2f}")
    print(f"  Total : {daily['y'].sum():,.2f}")

    return daily


def run_prophet_forecast(daily_data, forecast_days=30):

    try:
        from prophet import Prophet

        if len(daily_data) < FORECAST_CONFIG['min_data_points']:
            print(f"Not enough data: {len(daily_data)} days (need {FORECAST_CONFIG['min_data_points']})")
            return run_simple_forecast(daily_data, forecast_days)

        print(f"\nRunning Prophet model for {forecast_days} days...")

        model = Prophet(
            interval_width = FORECAST_CONFIG['confidence_interval'],
            yearly_seasonality = FORECAST_CONFIG['yearly_seasonality'],
            weekly_seasonality = FORECAST_CONFIG['weekly_seasonality'],
            daily_seasonality = FORECAST_CONFIG['daily_seasonality'],
            changepoint_prior_scale = 0.05,
        )

        model.fit(daily_data)

        future = model.make_future_dataframe(periods=forecast_days)
        forecast = model.predict(future)

        forecast['yhat'] = forecast['yhat'].clip(lower=0)
        forecast['yhat_lower'] = forecast['yhat_lower'].clip(lower=0)
        forecast['yhat_upper'] = forecast['yhat_upper'].clip(lower=0)

        future_only = forecast[forecast['ds'] > daily_data['ds'].max()]

        print(f"\nProphet Forecast Results ({forecast_days} days ahead):")
        print(f"  Predicted Total : {future_only['yhat'].sum():,.2f}")
        print(f"  Predicted Daily : {future_only['yhat'].mean():,.2f}")
        print(f"  Best Case (Upper) : {future_only['yhat_upper'].sum():,.2f}")
        print(f"  Worst Case (Lower) : {future_only['yhat_lower'].sum():,.2f}")

        return forecast, model

    except ImportError:
        print("Prophet not installed. Falling back to linear regression.")
        print("To install Prophet: pip install prophet")
        return run_simple_forecast(daily_data, forecast_days)

    except Exception as e:
        print(f"Prophet failed: {e}. Falling back to linear regression.")
        return run_simple_forecast(daily_data, forecast_days)


def run_simple_forecast(daily_data, forecast_days=30):

    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler

    print(f"\nRunning linear regression forecast for {forecast_days} days...")

    daily_data = daily_data.copy()
    daily_data['t'] = np.arange(len(daily_data))
    daily_data['t2'] = daily_data['t'] ** 2

    daily_data['day_of_week'] = daily_data['ds'].dt.dayofweek
    daily_data['month'] = daily_data['ds'].dt.month

    feature_cols = ['t', 'day_of_week', 'month']
    X = daily_data[feature_cols].values
    y = daily_data['y'].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LinearRegression()
    model.fit(X_scaled, y)

    last_date = daily_data['ds'].max()
    last_t = daily_data['t'].max()

    future_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
    future_t = [last_t + i + 1 for i in range(forecast_days)]

    future_df = pd.DataFrame({
        'ds': future_dates,
        't': future_t,
        'day_of_week': [d.weekday() for d in future_dates],
        'month': [d.month for d in future_dates],
    })

    X_future = scaler.transform(future_df[feature_cols].values)
    future_preds = model.predict(X_future)
    future_preds = np.clip(future_preds, 0, None)

    uncertainty = future_preds * 0.18

    hist_X_scaled = scaler.transform(daily_data[feature_cols].values)
    hist_preds = model.predict(hist_X_scaled)
    hist_preds = np.clip(hist_preds, 0, None)

    all_ds = list(daily_data['ds']) + future_dates
    all_yhat = list(hist_preds) + list(future_preds)
    all_lower = list(hist_preds * 0.85) + list(future_preds - uncertainty)
    all_upper = list(hist_preds * 1.15) + list(future_preds + uncertainty)

    all_lower = [max(0, v) for v in all_lower]

    forecast = pd.DataFrame({
        'ds': all_ds,
        'yhat': all_yhat,
        'yhat_lower': all_lower,
        'yhat_upper': all_upper,
    })

    forecast['ds'] = pd.to_datetime(forecast['ds'])

    future_only = forecast[forecast['ds'] > daily_data['ds'].max()]

    print(f"\nLinear Regression Forecast Results ({forecast_days} days ahead):")
    print(f"  Predicted Total : {future_only['yhat'].sum():,.2f}")
    print(f"  Predicted Daily : {future_only['yhat'].mean():,.2f}")
    print(f"  Best Case (Upper) : {future_only['yhat_upper'].sum():,.2f}")
    print(f"  Worst Case (Lower) : {future_only['yhat_lower'].sum():,.2f}")

    return forecast, model


def create_forecast_chart(daily_data, forecast, metric='revenue', forecast_days=30):

    last_hist_date = daily_data['ds'].max()
    hist_forecast = forecast[forecast['ds'] <= last_hist_date]
    future_forecast = forecast[forecast['ds'] > last_hist_date].head(forecast_days)

    is_currency = metric in ['revenue', 'profit']
    prefix = "$" if is_currency else ""
    metric_title = metric.replace('_', ' ').title()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x = pd.concat([future_forecast['ds'], future_forecast['ds'][::-1]]),
        y = pd.concat([future_forecast['yhat_upper'], future_forecast['yhat_lower'][::-1]]),
        fill = 'toself',
        fillcolor = 'rgba(102, 126, 234, 0.12)',
        line = dict(color='rgba(255,255,255,0)'),
        name = f"{int(FORECAST_CONFIG['confidence_interval']*100)}% Confidence Band",
        hoverinfo = 'skip',
        showlegend = True,
    ))

    fig.add_trace(go.Bar(
        x = daily_data['ds'],
        y = daily_data['y'],
        name = f'Actual {metric_title}',
        marker_color = 'rgba(102, 126, 234, 0.65)',
        hovertemplate = f'<b>%{{x|%b %d, %Y}}</b><br>Actual: {prefix}%{{y:,.2f}}<extra></extra>',
    ))

    fig.add_trace(go.Scatter(
        x = hist_forecast['ds'],
        y = hist_forecast['yhat'],
        mode = 'lines',
        name = 'Model Fit',
        line = dict(color='rgba(118, 75, 162, 0.7)', width=1.5, dash='dot'),
        hovertemplate = f'<b>%{{x|%b %d, %Y}}</b><br>Fitted: {prefix}%{{y:,.2f}}<extra></extra>',
    ))

    fig.add_trace(go.Scatter(
        x = future_forecast['ds'],
        y = future_forecast['yhat'],
        mode = 'lines+markers',
        name = f'Forecast ({forecast_days}d)',
        line = dict(color='#28a745', width=2.5),
        marker = dict(size=5, color='#28a745'),
        hovertemplate = f'<b>%{{x|%b %d, %Y}}</b><br>Predicted: {prefix}%{{y:,.2f}}<extra></extra>',
    ))

    fig.add_trace(go.Scatter(
        x = future_forecast['ds'],
        y = future_forecast['yhat_upper'],
        mode = 'lines',
        name = 'Best Case',
        line = dict(color='rgba(40, 167, 69, 0.5)', width=1.2, dash='dash'),
        hovertemplate = f'Best Case: {prefix}%{{y:,.2f}}<extra></extra>',
    ))

    fig.add_trace(go.Scatter(
        x = future_forecast['ds'],
        y = future_forecast['yhat_lower'],
        mode = 'lines',
        name = 'Worst Case',
        line = dict(color='rgba(220, 53, 69, 0.5)', width=1.2, dash='dash'),
        hovertemplate = f'Worst Case: {prefix}%{{y:,.2f}}<extra></extra>',
    ))

    fig.add_shape(
        type='line',
        x0=last_hist_date,
        x1=last_hist_date,
        y0=0,
        y1=1,
        yref='paper',
        line=dict(color='#ffc107', width=2, dash='dash'),
    )
    
    fig.add_annotation(
        x=last_hist_date,
        y=1,
        yref='paper',
        text='Forecast Start',
        showarrow=False,
        font=dict(color='#ffc107', size=12),
        yshift=10,
    )

    fig.update_layout(
        title = dict(
            text = f'📈 {metric_title} Forecast — Next {forecast_days} Days',
            font = dict(size=18, color='#1a1a2e'),
            x = 0.0,
        ),
        xaxis_title = 'Date',
        yaxis_title = f'{metric_title} ({prefix})',
        hovermode = 'x unified',
        height = 500,
        plot_bgcolor = 'white',
        paper_bgcolor = 'white',
        legend = dict(
            orientation = 'h',
            yanchor = 'bottom',
            y = 1.02,
            xanchor = 'right',
            x = 1,
        ),
        xaxis = dict(
            showgrid = True,
            gridcolor = 'rgba(0,0,0,0.05)',
            showline = True,
            linecolor = 'rgba(0,0,0,0.1)',
        ),
        yaxis = dict(
            showgrid = True,
            gridcolor = 'rgba(0,0,0,0.05)',
            tickprefix = prefix,
            showline = True,
            linecolor = 'rgba(0,0,0,0.1)',
        ),
    )

    return fig


def get_forecast_summary_table(daily_data, forecast, forecast_days=30):

    last_date = daily_data['ds'].max()
    future = forecast[forecast['ds'] > last_date].head(forecast_days).copy()

    if len(future) == 0:
        return pd.DataFrame()

    future['week_num'] = future['ds'].dt.isocalendar().week.astype(int)
    future['year'] = future['ds'].dt.year
    future['week_start'] = future['ds'].apply(lambda x: x - timedelta(days=x.weekday()))
    future['week_end'] = future['week_start'] + timedelta(days=6)
    future['week_label'] = future.apply(
        lambda r: f"{r['week_start'].strftime('%b %d')} - {r['week_end'].strftime('%b %d, %Y')}",
        axis=1
    )

    weekly = future.groupby('week_label').agg(
        predicted_total = ('yhat', 'sum'),
        best_case = ('yhat_upper', 'sum'),
        worst_case = ('yhat_lower', 'sum'),
        daily_avg = ('yhat', 'mean'),
        start_date = ('ds', 'min'),
    ).reset_index()

    weekly = weekly.sort_values('start_date').drop('start_date', axis=1)

    weekly.columns = ['Week', 'Predicted Total', 'Best Case', 'Worst Case', 'Daily Average']

    for col in ['Predicted Total', 'Best Case', 'Worst Case', 'Daily Average']:
        weekly[col] = weekly[col].round(2)

    return weekly


def calculate_forecast_metrics(daily_data, forecast, forecast_days=30):

    last_date = daily_data['ds'].max()
    future = forecast[forecast['ds'] > last_date].head(forecast_days)

    if len(future) == 0:
        return {}

    historical_avg = daily_data['y'].tail(forecast_days).mean()
    forecast_avg = future['yhat'].mean()

    if historical_avg > 0:
        expected_change_pct = (forecast_avg - historical_avg) / historical_avg * 100
    else:
        expected_change_pct = 0

    metrics = {
        'total_predicted': round(future['yhat'].sum(), 2),
        'daily_avg_predicted': round(future['yhat'].mean(), 2),
        'best_case_total': round(future['yhat_upper'].sum(), 2),
        'worst_case_total': round(future['yhat_lower'].sum(), 2),
        'expected_change_pct': round(expected_change_pct, 2),
        'forecast_days': forecast_days,
        'peak_day': future.loc[future['yhat'].idxmax(), 'ds'].strftime('%b %d, %Y'),
        'peak_day_value': round(future['yhat'].max(), 2),
        'lowest_day': future.loc[future['yhat'].idxmin(), 'ds'].strftime('%b %d, %Y'),
        'lowest_day_value': round(future['yhat'].min(), 2),
        'historical_daily_avg': round(historical_avg, 2),
    }

    return metrics


def run_full_forecast(df, metric='revenue', forecast_days=None):

    if forecast_days is None:
        forecast_days = FORECAST_CONFIG['forecast_days']

    print(f"\n{'='*55}")
    print(f"  FORECASTING: {metric.upper()} - {forecast_days} DAYS AHEAD")
    print(f"{'='*55}")

    daily_data = prepare_data_for_forecast(df, metric=metric)

    if len(daily_data) < FORECAST_CONFIG['min_data_points']:
        return {
            'success': False,
            'error': f"Need at least {FORECAST_CONFIG['min_data_points']} days of data. You have {len(daily_data)}.",
            'daily_data': daily_data,
        }

    result = run_prophet_forecast(daily_data, forecast_days=forecast_days)

    if result is None:
        return {
            'success': False,
            'error': 'Forecast model failed to run.',
        }

    forecast, model = result

    chart = create_forecast_chart(daily_data, forecast, metric=metric, forecast_days=forecast_days)
    summary_table = get_forecast_summary_table(daily_data, forecast, forecast_days=forecast_days)
    forecast_metrics = calculate_forecast_metrics(daily_data, forecast, forecast_days=forecast_days)

    print(f"\n-> Forecast complete!")
    print(f"   Predicted Total ({forecast_days}d) : {forecast_metrics.get('total_predicted', 0):,.2f}")
    print(f"   Expected Change : {forecast_metrics.get('expected_change_pct', 0):+.1f}%")
    print(f"   Peak Day : {forecast_metrics.get('peak_day', 'N/A')}")
    print(f"   Best Case Total : {forecast_metrics.get('best_case_total', 0):,.2f}")
    print(f"   Worst Case Total : {forecast_metrics.get('worst_case_total', 0):,.2f}")

    return {
        'success': True,
        'daily_data': daily_data,
        'forecast': forecast,
        'model': model,
        'chart': chart,
        'summary_table': summary_table,
        'metrics': forecast_metrics,
    }


if __name__ == '__main__':
    filepath = 'data/processed/sales_completed.csv'

    if not os.path.exists(filepath):
        print("ERROR: Data file not found.")
        print("Run these commands first:")
        print("  python data_generator.py")
        print("  python data_processor.py")
    else:
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])

        for metric in ['revenue', 'orders']:
            result = run_full_forecast(df, metric=metric, forecast_days=30)

            if result['success']:
                os.makedirs('reports', exist_ok=True)
                chart_file = f'reports/forecast_{metric}_preview.html'
                result['chart'].write_html(chart_file)
                print(f"\n📊 Chart saved: {chart_file}")
                print("   Open in your browser to see the interactive forecast\n")

                print(f"Weekly Breakdown ({metric}):")
                print(result['summary_table'].to_string(index=False))
                print()
            else:
                print(f"Forecast failed: {result['error']}")