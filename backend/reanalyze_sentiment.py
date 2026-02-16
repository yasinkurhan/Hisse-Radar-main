import sqlite3
import sys
import os
from pathlib import Path

# Backend root setup
BACKEND_ROOT = Path(__file__).parent
sys.path.append(str(BACKEND_ROOT))

try:
    from app.services.news_sentiment_service import SentimentAnalyzer
except ImportError:
    print("Could not import SentimentAnalyzer. Make sure you are running from backend directory.")
    sys.exit(1)

DB_PATH = BACKEND_ROOT / "app" / "data" / "kap_news.db"

def reanalyze():
    print(f"Connecting to database: {DB_PATH}")
    if not DB_PATH.exists():
        print("Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, summary, category FROM kap_news")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} news items to re-analyze...")
    
    updated_count = 0
    for row in rows:
        news_id, title, summary, category = row
        text = f"{title} {summary or ''}"
        
        # Advanced Text Analysis
        result = SentimentAnalyzer.analyze_text(text)
        base_score = result["score"]
        
        # Category Modifier
        cat_info = SentimentAnalyzer.KAP_CATEGORIES.get(category, {"sentiment_modifier": 0})
        mod = cat_info["sentiment_modifier"]
        
        # Final Score
        final_score = base_score + mod
        final_score = max(-1.0, min(1.0, final_score))
        
        # Recalculate Label
        new_label_enum = SentimentAnalyzer._score_to_sentiment(final_score)
        new_label = new_label_enum.value
        
        cursor.execute("""
            UPDATE kap_news 
            SET sentiment_score = ?, sentiment_label = ?
            WHERE id = ?
        """, (final_score, new_label, news_id))
        updated_count += 1
        
        if updated_count % 50 == 0:
            print(f"Processed {updated_count} items...")
            
    conn.commit()
    conn.close()
    print(f"Completed! Updated {updated_count} news items with new sentiment logic.")

if __name__ == "__main__":
    reanalyze()
