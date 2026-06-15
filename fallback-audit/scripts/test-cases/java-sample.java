// F001: bare catch-all returning null
public User findUser(String id) {
    try {
        return repository.findById(id);
    } catch (Exception e) {
        return null;
    }
}

// F001: bare catch-all returning empty list
public List<Item> getItems() {
    try {
        return dao.fetchAll();
    } catch (Exception e) {
        return Collections.emptyList();
    }
}

// F002: silent catch
public void save(Record record) {
    try {
        persist(record);
    } catch (Exception e) {
    }
}

// F003: Optional null-masking with orElse(null)
public String getEmail(User user) {
    return Optional.ofNullable(user).map(u -> u.getEmail()).orElse(null);
}

// F003: Optional null-masking with orElse("")
public String getDisplayName(User user) {
    return Optional.ofNullable(user).map(u -> u.getName()).orElse("");
}

// F005: empty collection return in catch
public List<Order> getOrders(int customerId) {
    try {
        return repository.findByCustomer(customerId);
    } catch (Exception e) {
        return new ArrayList<>();
    }
}

// F008: orElse with constant (always evaluated)
public User getUser(String id) {
    return findUser(id).orElse(createDefaultUser());
}

// Legitimate: orElseGet is fine
public User getUserSafe(String id) {
    return findUser(id).orElseGet(() -> createDefaultUser());
}
