// F001: bare catch-all returning null
public class OrderService {
    public Order GetOrder(int id) {
        try {
            return _repo.GetOrder(id);
        } catch (Exception e) {
            return null;
        }
    }

    // F005: empty collection fallback
    public IEnumerable<Order> GetOrders(int customerId) {
        try {
            return _repo.GetOrders(customerId);
        } catch {
            return Enumerable.Empty<Order>();
        }
    }

    // F002: silent catch
    public void LogOrder(Order order) {
        try {
            _audit.Log(order);
        } catch (Exception) {
        }
    }

    // F004: null coalesce chain
    public string GetDisplayName(User user) {
        string s = user.DisplayName ?? user.UserName ?? user.Email ?? "Anonymous";
        return s;
    }

    // Legitimate: single null coalesce
    public string GetName(User user) {
        return user?.DisplayName ?? "Anonymous";
    }
}
