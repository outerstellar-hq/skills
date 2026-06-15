// F003: null masking with Elvis
class ProductService {
    fun getPrice(product: Product?): BigDecimal {
        return product?.price ?: 0
    }

    fun getName(product: Product?): String {
        return product?.name ?: ""
    }

    fun getTags(product: Product?): List<String> {
        return product?.tags ?: emptyList()
    }
}

// F001: bare catch-all returning default
class DataService {
    fun fetch(id: String): Data {
        return try {
            callApi(id)
        } catch (e: Exception) {
            return Data()  // Return empty data on any error
        }
    }
}

// F002: silent catch
class LogService {
    fun send(event: Event) {
        try {
            transport.send(event)
        } catch (e: Exception) {
        }
    }
}

// F012: runCatching getOrDefault
class ResilienceService {
    fun getValue(key: String): String {
        return runCatching { lookup(key) }.getOrDefault("")
    }
}
