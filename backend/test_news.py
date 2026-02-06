import asyncio
from app.services.real_news_service import GoogleNewsService, FinansHaberService, RealNewsAggregator

async def test():
    try:
        print('Testing Google News...')
        news = await GoogleNewsService.fetch_market_news(5)
        print(f'Google News result: {len(news)} haberler')
        
        print('Testing Finans Haber...')
        fnews = await FinansHaberService.fetch_all_finance_news(5)
        print(f'Finans result: {len(fnews)} haberler')
        
        print('Testing Market Summary...')
        summary = await RealNewsAggregator.get_market_summary()
        score = summary.get('market_sentiment_score', 0)
        total = summary.get('total_news', 0)
        print(f'Summary: sentiment={score}, news={total}')
        
    except Exception as e:
        import traceback
        print(f'HATA: {type(e).__name__}: {e}')
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test())
