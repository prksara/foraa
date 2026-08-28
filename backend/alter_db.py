import sqlite3

def run():
    conn = sqlite3.connect('foraa.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE health_goals ADD COLUMN progress FLOAT")
        print("Added progress column to health_goals")
    except Exception as e:
        print("Error adding progress:", e)
        
    try:
        cursor.execute("ALTER TABLE health_goals ADD COLUMN start_date DATE")
        print("Added start_date column to health_goals")
    except Exception as e:
        print("Error adding start_date:", e)
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    run()
