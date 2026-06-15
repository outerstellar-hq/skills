# F010: except: pass — most dangerous pattern
def process_data(data):
    try:
        result = transform(data)
        save(result)
    except:
        pass


# F001: bare except returning None
def find_user(user_id):
    try:
        return db.query("SELECT * FROM users WHERE id = ?", user_id)
    except:
        return None


# F002: silent except with only a comment
def silent_fail(data):
    try:
        risky_call(data)
    except:
        # expected to fail sometimes


# F005: except returning empty collection
def get_items(category):
    try:
        return api.fetch_items(category)
    except:
        return []


# F005: except returning empty dict
def get_config():
    try:
        return load_config_file()
    except:
        return {}


# F004: or-chain fallback
def get_timeout():
    timeout = config.get("timeout") or config.get("default_timeout") or 30
    return timeout


# F007: catch-log-continue (logger without re-raise)
def process_orders(orders):
    for order in orders:
        try:
            process(order)
        except Exception as e:
            logger.error("Failed to process order %s: %s", order.id, e)


# F003: dict.get with silent default
def get_retry_count():
    return config.get("retries", 3)


# Legitimate: dict.get for optional key with None default is fine
tag = metadata.get("tag", None)
