import sqlite3
from time import time

db = 'data/newdb.db'


def create_tables(db):
    create_users = """CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT,
        password_hash TEXT,
        email TEXT,
        doc INT,
        dom INT
    )
    """

    create_cards = """CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deck_id INTEGER,
        template_id INTEGER,
        format_id INTEGER,
        modified INT,
        data TEXT,
        isPublic INT,
        isDeleted INT,
        created_uid INT
    )
    """

    create_user_cards = """CREATE TABLE IF NOT EXISTS user_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INT,
        cid INT,
        ef INT,
        ivl INT,
        type INT,
        status INT,
        reps INT,
        lapses INT,
        odue INT,
        due INT,
        left INT,
        isDeleted INT
    )
    """

    create_decks = """CREATE TABLE IF NOT EXISTS decks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        desc TEXT,
        created INT,
        modified INT,
        created_uid INT,
        total_cards INT,
        isPublic INT,
        isDeleted INT
    )
    """

    create_user_decks = """CREATE TABLE IF NOT EXISTS user_decks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER,
        deck_id INTEGER,
        config_id INT,
        FOREIGN KEY(uid) REFERENCES users(id),
        FOREIGN KEY(deck_id) REFERENCES decks(id)
    )
    """

    # does the 'fields' field need to be json? Could also use an auxiliary table for each template but that could become
    # convoluted, could also try comma separated values.
    # sortfield generated automatically from first field in template
    # need two template tables? One for general templates for creating card specific ones and one to store those?

    create_templates = """ CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        fields TEXT,
        sortfield TEXT,
        modified INT,
        created_uid INT,
        front_format TEXT,
        back_format TEXT,
        styling TEXT
                )
    """

    # create_formats = """CREATE TABLE IF NOT EXISTS formats (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     name TEXT,
    #     template_id INT,
    #     creator_id INT,
    #     front TEXT,
    #     back TEXT,
    #     styling TEXT,
    #     modified INT,
    #     foreign key (template_id) REFERENCES templates(id)
    # )
    # """

    create_configs = """CREATE TABLE IF NOT EXISTS configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INT,
        new_delays TEXT,
        new_grad_ivls TEXT,
        new_init_ef INT,
        new_per_day INT,
        rev_per_day INT,
        rev_easy_factor INT,
        rev_hard_factor INT,
        max_ivl INT,
        lapse_delays TEXT,
        lapse_percent INT,
        min_ivl INT,
        leech_fails INT,
        name TEXT
        )
        """

    create_revlog = """CREATE TABLE IF NOT EXISTS revlog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ucid INT,
        ease INT,
        ivl INT,
        lastivl INT,
        ef INT,
        lastef INT,
        status INT,
        reps INT,
        lapses INT,
        time INT,
        lasttime INT,
        start INT,
        end INT
    )
    """


    conn = sqlite3.connect(db)
    cur = conn.cursor()
    create_statements = [create_users, create_cards, create_user_cards, create_decks, create_user_decks,
                         create_templates, create_configs, create_revlog]
    for statement in create_statements:
        cur.execute(statement)
    conn.commit()
    conn.close()


con = sqlite3.connect(db)
cur = con.cursor()
# cur.execute("DROP TABLE templates")
# cur.execute("DROP TABLE user_cards")

cur.execute("""DROP TABLE cards""")
create_tables(db)


# cur.execute("""SELECT * FROM formats""")
# cur.execute(f"""INSERT INTO formats (name, template_id, creator_id, modified) VALUES ('basic', 1, 1, {time()})""")
print(cur.fetchall())
con.commit()
cur.close()
con.close()
