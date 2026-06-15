// F009: unwrap_or with constructed default
fn load_config() -> Config {
    parse_config_file("config.toml").unwrap_or(Config::default())
}

// F009: unwrap_or_default (always produces default on failure)
fn get_connection() -> Connection {
    connect_to_db().unwrap_or_default()
}

// F009: unwrap_or with boolean constant
fn is_feature_enabled(name: &str) -> bool {
    lookup_feature(name).unwrap_or(false)
}

// F012: catch_all on unstable operation
fn process_batch(items: Vec<Item>) {
    items.par_iter().try_for_each(|item| {
        catch_all(|| process_item(item))
    });
}

// Legitimate: match with Ok/Err handling
fn lookup(id: &str) -> Result<User, Error> {
    db.find_user(id).map_err(|e| Error::NotFound(id.into()))
}
