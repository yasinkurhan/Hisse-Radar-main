from app.services.analysis_service import get_analysis_service
print(get_analysis_service().run_daily_analysis(limit=1, index_filter='BIST30').get('all_results')[0].keys())
