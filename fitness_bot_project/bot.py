# ... (здесь идут все остальные функции: init_db, add_user, load_post, send_post_to_user и т.д.) ...

async def check_and_send_posts():
    """Фоновая проверка и отправка постов по индивидуальным интервалам"""
    intervals = config.get("INTERVALS_SECONDS", [0]*8)
    users = get_all_users()
    
    for user_id in users:
        sent_count = get_user_post_count(user_id)
        if sent_count >= 8: continue  # Все посты уже отправлены
            
        next_post_num = sent_count + 1
        required_interval = intervals[sent_count] if sent_count < len(intervals) else 0
        
        if required_interval > 0:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sent_at FROM post_history 
                WHERE user_id = ? AND post_number = ? 
                ORDER BY sent_at DESC LIMIT 1
            ''', (user_id, sent_count))
            last_sent = cursor.fetchone()
            conn.close()
            
            if last_sent:
                last_time = datetime.fromisoformat(last_sent[0].replace('+00:00', ''))
                elapsed = (datetime.now() - last_time).total_seconds()
                if elapsed < required_interval: continue  # Интервал ещё не прошёл
                
        await send_post_to_user(user_id, next_post_num)

def setup_scheduler():
    # Проверяем пользователей каждые 60 секунд
    scheduler.add_job(check_and_send_posts, 'interval', seconds=60, id='post_checker')
    scheduler.start()

async def on_startup(dispatcher):
    init_db()
    setup_scheduler()  # ← запускаем планировщик при старте бота
    print("✅ Бот